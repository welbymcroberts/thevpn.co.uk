from django.db import models
from django.contrib.auth.models import User
from django_ca.models import Certificate


class AS(models.Model):
    number = models.IntegerField()


class Country(models.Model):
    region = models.IntegerField()
    countrycode = models.IntegerField
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

    def __unicode__(self):
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

    def __str__(self):
        return "%s (%s)" %(self.dns, self.routertype)
