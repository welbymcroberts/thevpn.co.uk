from django import forms
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Router, RouterType, VPNProtocol, VPNServer, AS
from django_ca.models import Certificate
from ca.views import RevokeForm
from ca.helpers import get_duplicates_by_cn
from django_countries.fields import Country
#from django_countries.widgets import CountrySelectWidget
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import datetime
from django.utils.timesince import timesince
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout,Field,Submit,HTML
from crispy_forms.bootstrap import FormActions

from ca.helpers import create_cert
from .helpers import get_next_ASN, make_random_string

class RouterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RouterForm, self).__init__(*args, **kwargs)
        helper = self.helper = FormHelper(self)
    
        # Moving field labels into placeholders
        layout = helper.layout = Layout()
        for field_name, field in self.fields.items():
            if field_name == "routertype":
                self.fields[field_name].widget = forms.RadioSelect(attrs={})
                self.fields[field_name].choices = [(x, y) for x,y in self.fields[field_name].choices if x != '' ]


            if field.initial is not None:
                layout.append(Field(field_name, placeholder=field.initial ))
                field.initial = ""
            else:
                layout.append(Field(field_name))
        #helper.form_show_labels = False
        layout.append(FormActions(
            Submit('submit', 'Create', css_class="btn btn-primary pull-right"),
            HTML('<a href="/" class="btn btn-info">Cancel</a>'),
            ))

    supported_client_protocols = forms.ModelMultipleChoiceField(queryset=VPNProtocol.objects.all())
    supported_server_protocols = forms.ModelMultipleChoiceField(queryset=VPNServer.objects.all())
    
    class Meta:
        model = Router
        fields = [
            'dns',
            'description',
            'routertype',
            'auto_connect',
            'country',
            'supported_client_protocols',
            'supported_server_protocols',
        ]

@login_required
def list_routers(request):
    routers = Router.objects.filter(owner=request.user);
    
    if request.user.is_staff:
        other_routers = Router.objects.exclude(owner=request.user);
    else:
        other_routers = None
        
    return render(request, 'routing/index.html', { 'routers': routers, 'other_routers': other_routers });

@login_required
def create_router(request):
    form = RouterForm()

    if request.method == 'POST':
        form = RouterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            dns = data.get('dns')
            country = Country(data.get('country'))
            
            #key,cert = create_cert(
            #    dns,
            #    country.code,
            #    settings.THEVPN_NAME,
            #    settings.THEVPN_NAME,
            #    {dns,}
            #)
            
            ASN = AS(number=get_next_ASN(country.numeric, country.region - 900))
            ASN.save()
            router = Router(
                dns=dns,
                description=data.get('description'),
                routertype=data.get('routertype'),
                auto_connect=data.get('auto_connect'),
                endpointkey=make_random_string(32),
                radiuskey=make_random_string(32),
                country=country,
                ASN=ASN,
                #certificate=cert,
                #TODO: should we check this is a valid and authed user?
                owner=request.user,
            )
            router.save()
            router.supported_client_vpn_protocols = data.get('supported_client_protocols')
            router.supported_server_vpn_protocols = data.get('supported_server_protocols')
            router.save()
            # TODO - itterate over all Routers that are autoconnect and setup a connection between them
            return redirect('/');
            #return render(request, 'ca/oneshot_certificate.html', {'key': key, 'cert': cert.pub})
    
    return render(request, 'routing/create_router.html', {'form': form})

@login_required
def delete_router(request, endpointkey):
    # Check against a router
    if request.user.is_staff:
        router = get_object_or_404(Router, endpointkey=endpointkey)
    else:
        router = get_object_or_404(Router, endpointkey=endpointkey, owner=request.user)
    
    router_dns = router.dns
    router.delete();
    
    messages.add_message(request, messages.SUCCESS, 'Router \'%s\' has been removed' % router_dns)

    return redirect('/')

@login_required
def show_certificate(request, endpointkey = None, serial = None):
    if endpointkey == None and serial == None:
        raise Http404('No Certificate')
    elif endpointkey is not None:
        if request.user.is_staff:
            router = get_object_or_404(Router, endpointkey=endpointkey)
        else:
            router = get_object_or_404(Router, endpointkey=endpointkey, owner=request.user)

        cert = router.certificate
        
        if cert is not None:
            cert.isLinked = True
    elif serial is not None:
        cert = get_object_or_404(Certificate, serial=serial)
        cert.isLinked = False
        
        try:
            router = Router.objects.get(dns=cert.cn)
            if not request.user.is_staff and router.owner != request.user:
                return redirect('/')

            cert.isLinked = router is not None and cert.id == router.certificate.id
        except:
            router = None
        
    revokeForm = None
    canRequest = False
    duplicateCerts = None
    if cert is None:
        canRequest = True
    else:
        if not cert.revoked and request.user.is_active and (request.user.is_staff or (router is not None and router.owner == request.user)):
            revokeForm = RevokeForm()
        if not cert.revoked:
            cert.revoked_date = "No"
    
        duplicateCerts = get_duplicates_by_cn(cert)
        
        if cert.revoked:
            canRequest = True
            for dupCert in duplicateCerts:
                if not dupCert.revoked:
                    canRequest = False
                    break
    
    return render(request, 'routing/show_certificate.html', {'router': router, 'cert': cert, 'duplicateCerts': duplicateCerts, 'revokeForm': revokeForm, 'canRequest' : canRequest})

@login_required
def activate_certificate(request, serial):
    if not request.user.is_active:
        return HttpResponse(status=403)

    cert = Certificate.objects.get(serial=serial)
    
    if cert.revoked:
        messages.add_message(request, messages.WARNING, 'You can not activate a revoked certificate')
    else:
        router = Router.objects.filter(dns=cert.cn).first()
        
        if request.user.is_staff or router.owner == request.user:
            router.certificate = cert
            router.save()
            
            messages.add_message(request, messages.SUCESS, 'This certificate has been activated for router %s' % router.dns)
        else:
            messages.add_message(request, messages.ERROR, 'You are not allowed to activate this certificate')
        
    return redirect('/routing/certificate/show/%s' % serial)


@login_required
def revoke_certificate(request, serial):
    if request.method != 'POST' or not request.user.is_active:
        return HttpResponse(status=403)
    else:
        reason = request.POST.get('reason')
        
        if not reason or reason == "":
            messages.add_message(request, messages.WARNING, 'Please indicate the revocation reason')
        else:
            cert = Certificate.objects.get(serial=serial)
            
            if cert.revoked:
                messages.add_message(request, messages.WARNING, 'Certificate has already been revoked')
            else:
                router = Router.objects.filter(dns=cert.cn).first()
                
                if request.user.is_staff or (router is not None and router.owner == request.user):
                    cert.revoke(reason=reason)
                    messages.add_message(request, messages.SUCCESS, 'This certificate has been revoked')
                else:
                    messages.add_message(request, messages.ERROR, 'You are not allowed to revoke this certificate')

        return redirect('/routing/certificate/show/%s' % serial)


@login_required
def request_certificate(request, endpointkey):
    # Check against a router
    if request.user.is_staff:
        router = get_object_or_404(Router, endpointkey=endpointkey)
    else:
        router = get_object_or_404(Router, endpointkey=endpointkey, owner=request.user)
    
    hasCert = Certificate.objects.filter(cn=router.dns, revoked=False).count()
    if hasCert > 0:
        messages.add_message(request, messages.ERROR, 'A certificate with this CN already exists')
        return redirect('/routing/certificate/show/%s' % endpointkey)

    key,cert = create_cert(
        router.dns,
        router.country.code,
        settings.THEVPN_NAME,
        settings.THEVPN_NAME,
        {router.dns,}
    )

    router.certificate = cert
    router.save()
    
    return render(request, 'ca/oneshot_certificate.html', {'key': key, 'cert': cert.pub})


@login_required
def router_script(request, endpointkey):
    # Check against a router
    if request.user.is_staff:
        router = get_object_or_404(Router, endpointkey=endpointkey)
    else:
        router = get_object_or_404(Router, endpointkey=endpointkey, owner=request.user)
    
    import os.path
    scriptFile = os.path.join(settings.BASE_DIR, router.routertype.script);
    
    if not os.path.isfile(scriptFile):
        messages.add_message(request, messages.WARNING, 'No script file available for router type \'%s\', please check config and add a script file' % router.routertype)
        return redirect('/')
    
    from .helpers import file_get_contents
    script = file_get_contents(router.routertype.script)
    
    if router.routertype.name == "routeros6":
        from socket import gethostbyname, gaierror
        try:
            ip = gethostbyname(router.dns)
        except gaierror:
            ip = str(router.id >> 24 & 255) + "."
            ip+= str(router.id >> 16 & 255) + "."
            ip+= str(router.id >> 8 & 255) + "."
            ip+= str(router.id >> 0 & 255)
        
        script = script.replace(':local VPNAPIKEY "aaaaaaaaa"', ':local VPNAPIKEY "' + router.endpointkey + '"');
        script = script.replace(':local ASN "123456789"', ':local ASN "' + str(router.ASN) + '"');
        script = script.replace(':local ROUTERID "1.2.3.4"', ':local ROUTERID "' + ip + '"');
        script = script.replace(':local PREFIX "TheVPN"', ':local PREFIX "' + settings.THEVPN_NAME + '"');
        script = script.replace(':local BASEURL "https://thevpn.co.uk/"', ':local BASEURL "https://' + settings.THEVPN_FQDN + '/"');
    
    return HttpResponse(script, content_type="text/plain")
    
@login_required
def graph(request, type):
    routers = Router.objects.all()
    
    current_time = datetime.datetime.now(datetime.timezone.utc)

    for router in routers:
        found_peers = []
        router.all_peers = []

        if type == "status":
            if router.lastSeen is None:
                router.timeAgo = -1
            else:
                router.timeAgo = current_time.timestamp() - router.lastSeen.timestamp()
        else:
            router.timeAgo = "null"
        
        peers = router.get_peers()
        for peer in peers:
            if type != "peers" or not (request.user.is_staff or peer['owner'] == request.user.username or peer['neighbour'] == request.user):
                peer['myip'] = ""
                peer['remip'] = ""
                
                
            router.all_peers.append(peer)
            found_peers.append(peer['id'])
            
        for router2 in routers:
            if router.id is not router2.id and router2.id not in found_peers:
                router.all_peers.append({'id': router2.id})
    
    return render(request, 'routing/graph.html', { 'routers': routers, 'type': type });
    

def peer_list(request, endpointkey):
    # Check against a router
    router = get_object_or_404(Router, endpointkey=endpointkey)
    # TODO: only show peers we're connecting to.
    routers =   router.get_peers()
    template = 'routing/peers.html'
    if request.META['HTTP_USER_AGENT'] == 'Mikrotik/6.x Fetch':
        router.lastSeen = timezone.now()
        router.save()
        template = 'routing/peers.mikrotik'

    return render(request, template, {'routers': routers})

def ping(request, endpointkey):
    router = get_object_or_404(Router, endpointkey=endpointkey)
    
    if not   router.routertype.ping_allowed:
        content = "<html><body>"
        content+= "<h3>403 Forbidden</h3>"
        content+= "<p>This router type is not allowed to ping explicitly, install the supplied router script to automatically retrieve and set the peer configuration"
        content+= "</body></html>"
        return HttpResponse(content=content, status=403)
    else:
        router.lastSeen = timezone.now()
        router.save()
        return HttpResponse(status=204)
