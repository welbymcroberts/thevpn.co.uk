from django.conf import settings # import the settings file

def common(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return { 
                    'THEVPN_NAME': settings.THEVPN_NAME,
                    'THEVPN_FQDN': settings.THEVPN_FQDN,
                    }
