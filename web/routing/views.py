from django import forms
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from .models import Router, VPNProtocol, VPNServer, AS, Country
from django_ca.models import Certificate
from django.contrib.auth.decorators import login_required
from ca.helpers import create_cert
from .helpers import get_next_ASN, make_random_string


class RouterForm(forms.ModelForm):
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
def create_router(request):
    form = RouterForm()
    if request.method == 'POST':
        form = RouterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            dns = data.get('dns')
            country = data.get('country')
            key,cert = create_cert(
                dns,
                country.shortname,
                settings.THEVPN_NAME,
                settings.THEVPN_NAME,
                {dns,}
            )
            ASN = AS(number=get_next_ASN(country.countrycode,country.region))
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
                certificate=Certificate.objects.get(pub=cert),
                #TODO: should we check this is a valid and authed user?
                owner=request.user,
            )
            router.save()
            router.supported_client_vpn_protocols = data.get('supported_client_protocols')
            router.supported_server_vpn_protocols = data.get('supported_server_protocols')
            router.save()
            # TODO - itterate over all Routers that are autoconnect and setup a connection between them
            return render(request, 'ca/oneshot_certificate.html', {'key': key, 'cert': cert})
    return render(request, 'routing/create_router.html', {'form': form})


def peer_list(request,endpointkey):
    # Check against a router
    requesting_router = get_object_or_404(Router, endpointkey=endpointkey)
    # TODO: only show peers we're connecting to.
    routers = requesting_router.get_peers()
    template = 'routing/peers.html'
    if request.META['HTTP_USER_AGENT'] == 'Mikrotik/6.x Fetch':
        template = 'routing/peers.mikrotik'
    return render(request, template, {'routers': routers})
