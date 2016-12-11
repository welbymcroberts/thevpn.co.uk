from django.contrib import admin
from .models import AS, Router, Country, VPNProtocol, VPNServer, RouterType, RouterConnection

# Register your models here.
admin.site.register(AS)
admin.site.register(Country)
admin.site.register(VPNProtocol)
admin.site.register(VPNServer)
admin.site.register(RouterType)



class FromRouterConnectionInline(admin.TabularInline):
    model = RouterConnection
    extra = 1
    fk_name = 'from_router'

class ToRouterConnectionInline(admin.TabularInline):
    model = RouterConnection
    extra = 1
    fk_name = 'to_router'


class RouterAdmin(admin.ModelAdmin):
    inlines = (FromRouterConnectionInline,ToRouterConnectionInline,)


admin.site.register(Router, RouterAdmin)