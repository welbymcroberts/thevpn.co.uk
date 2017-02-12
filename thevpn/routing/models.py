from django.db import models
from django.contrib.auth.models import User
from django_ca.models import Certificate
from ipam.models import IPNetwork
from django_countries import Countries, Regions
from django_countries.fields import CountryField
import netaddr

class AS(models.Model):
    number = models.BigIntegerField()

    def __str__(self):
        return "%s" %self.number


#class Country(models.Model):
#    region = models.IntegerField()
#    countrycode = models.IntegerField()
#   shortname = models.CharField(max_length=4)
#   name = models.CharField(max_length=255)
#    
#    def __str__(self):
#        return self.name


class VPNProtocol(models.Model):
    name = models.CharField(max_length=50, default="")
    shortname = models.CharField(max_length=10, default="")

    def __str__(self):
        return self.name


class VPNServer(models.Model):
    protocol = models.ForeignKey(VPNProtocol)
    port = models.IntegerField(blank=False, null=False)

    def __str__ (self):
        return "%s on port %s" %(self.protocol, self.port)


class RouterType(models.Model):
    name = models.CharField(max_length=50, default="")
    script = models.CharField(max_length=50, default="", blank=True)
    ping_allowed = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class RouterConnection(models.Model):
    vpn_server = models.ForeignKey(VPNServer)
    from_router = models.ForeignKey('Router', related_name='from_router')
    to_router = models.ForeignKey('Router', related_name='to_router')
    iprange = models.ForeignKey(IPNetwork)
    class Meta:
        unique_together = ('from_router', 'to_router')

class ITURegions(Regions):
    only = {
        900: "ITU World",
        901: "ITU Region 1",
        902: "ITU Region 2",
        903: "ITU Region 3",
    }
    map_only_lookup = True
    map_only = {
        900: [901, 901, 903],
        901: [2, 143, 145, 150, 496],
        902: [19],
        903: [9, 30, 34, 35, "!496"],
    }

class ITUCountries(Countries):
    regions = ITURegions()
    use_regions = True

class Router(models.Model):
    dns = models.CharField(max_length=255, unique=True, default="no.hostname.provided")
    owner = models.ForeignKey(User)
    description = models.TextField()
    routertype = models.ForeignKey(RouterType)
    supported_client_vpn_protocols = models.ManyToManyField(VPNProtocol, blank=True)
    supported_server_vpn_protocols = models.ManyToManyField(VPNServer, blank=True)
    endpointkey = models.CharField(max_length=256)
    radiuskey = models.CharField(max_length=64)
    # TODO: username / password model for XAUTH or PPP?
    auto_connect = models.BooleanField(default=True)
    #country = models.ForeignKey(Country)
    country = CountryField(countries=ITUCountries)
    lastSeen = models.DateTimeField(default=None, null=True, blank=True)
    
    certificate = models.ForeignKey(Certificate, null=True, blank=True)
    ASN = models.ForeignKey(AS)
    peers = models.ManyToManyField('self', through='RouterConnection', symmetrical=False, related_name='related_peers+')
    
    def __str__(self):
        return "%s (%s)" %(self.dns, self.routertype)

    def generate_peer(self,peer):
        ret = {}
        my_offset = 1
        their_offset = 2
        if ((self.id == peer.from_router.id and peer.to_router.id < peer.from_router.id) 
           or (self.id == peer.to_router.id and peer.to_router.id > peer.from_router.id)):
            my_offset = 2
            their_offset = 1
        if self.id == peer.from_router.id:
           ret['owner'] = peer.to_router.owner.username
           ret['neighbour'] = peer.from_router.owner.username
           ret['id'] = peer.to_router.id
           ret['dns'] = peer.to_router.dns
           ret['asn'] = peer.to_router.ASN.number
        else:
            ret['owner'] = peer.from_router.owner.username
            ret['neighbour'] = peer.to_router.owner.username
            ret['id'] = peer.from_router.id
            ret['dns'] = peer.from_router.dns
            ret['asn'] = peer.from_router.ASN.number
        ret['myip'] = "%s/%s" %((netaddr.IPAddress(peer.iprange.address) + my_offset),peer.iprange.size)
        ret['remip'] = "%s/%s" %((netaddr.IPAddress(peer.iprange.address) + their_offset),peer.iprange.size)
        ret['bgpip'] = "%s" %((netaddr.IPAddress(peer.iprange.address) + their_offset))
        ret['protocol'] = peer.vpn_server.protocol.shortname
        ret['port'] = peer.vpn_server.port
        return ret

    def get_peers(self):
        peer_list = []
        connect_to = RouterConnection.objects.filter(models.Q(from_router=self) | models.Q(to_router=self)).select_related()
        for peer in connect_to:
            peer_gen = self.generate_peer(peer)
            peer_list.append(peer_gen)
        return peer_list

    def add_peering(self,lhs,rhs,vpn_server, iprange):
        peering = RouterConnection.objects.get_or_create(from_router=lhs, to_router=rhs, iprange=iprange,
                                                         vpn_server=vpn_server)
        return peering

    def create_peering(self,lhs,rhs,vpn_server,iprange=None):
        if iprange==None:
            iprange = IPNetwork.objects.filter(size=30,in_use=False).order_by('id').first()
            iprange.in_use=True
            iprange.save()
        lhs.add_peering(lhs, rhs, vpn_server, iprange)
        rhs.add_peering(rhs, lhs, vpn_server, iprange)
        lhs.save()
        rhs.save()
        return lhs,rhs
