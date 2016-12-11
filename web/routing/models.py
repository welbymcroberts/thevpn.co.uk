from django.db import models
from django.contrib.auth.models import User
from django_ca.models import Certificate
from ipam.models import IPNetwork

class AS(models.Model):
    number = models.BigIntegerField()

    def __str__(self):
        return "%s" %self.number


class Country(models.Model):
    region = models.IntegerField()
    countrycode = models.IntegerField()
    shortname = models.CharField(max_length=4)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.name


class Router(models.Model):
    dns = models.CharField(max_length=255,default="no.hostname.provided")
    owner = models.ForeignKey(User)
    description = models.TextField()
    routertype = models.ForeignKey(RouterType)
    supported_client_vpn_protocols = models.ManyToManyField(VPNProtocol, blank=True)
    supported_server_vpn_protocols = models.ManyToManyField(VPNServer, blank=True)
    endpointkey = models.CharField(max_length=256)
    radiuskey = models.CharField(max_length=64)
    # TODO: username / password model for XAUTH or PPP?
    auto_connect = models.BooleanField(default=True)
    country = models.ForeignKey(Country)
    certificate = models.ForeignKey(Certificate)
    ASN = models.ForeignKey(AS)
    peers = models.ManyToManyField('self', through='RouterConnection', symmetrical=False, related_name='related_peers+')
    def __str__(self):
        return "%s (%s)" %(self.dns, self.routertype)


class RouterConnection(models.Model):
    vpn_server = models.ForeignKey(VPNServer)
    from_router = models.ForeignKey('Router', related_name='from_routers')
    to_router = models.ForeignKey('Router', related_name='to_routers')
    iprange = models.ForeignKey(IPNetwork)
    class Meta:
        unique_together = ('from_router', 'to_router')
