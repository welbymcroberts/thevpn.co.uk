from django.contrib import admin
from .models import AS, Router, Country, VPNProtocol, VPNServer, RouterType

# Register your models here.
admin.site.register(AS)
admin.site.register(Router)
admin.site.register(Country)
admin.site.register(VPNProtocol)
admin.site.register(VPNServer)
admin.site.register(RouterType)
