from django import forms
from django.shortcuts import render
from .models import Router, VPNProtocol, VPNServer, AS, Country
from django_ca.models import Certificate
from ca.helpers import create_cert
from .helpers import get_next_ASN


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


def create_router(request):
    form = RouterForm()
    if request.method == 'POST':
        form = RouterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            dns = data.get('dns')
            country = data.get('country')
            country_object = Country.objects.get(pk=country)
            countrycode = country_object.countrycode
            countryitu = country_object.region
            #key,cert = create_cert(
            #    dns,
            #    country.shortname,
            #    'TheVPN',
            #    'TheVPN',
            #    {dns,}
            #)
            cert = Certificate.objects.get(pk=1)
            ASN = AS(number=get_next_ASN(countrycode,countryitu))
            ASN.save()
            router = Router(
                dns=dns,
                description=data.get('description'),
                routertype=data.get('routertype'),
                auto_connect=data.get('auto_connect'),
                endpointkey='a',
                radiuskey='a',
                country=country,
                ASN=ASN,
                certificate=cert,
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