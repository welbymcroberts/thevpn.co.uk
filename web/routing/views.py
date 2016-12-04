from django import forms
from django.shortcuts import render
from .models import Router, VPNProtocol, VPNServer
from ca.helpers import create_cert

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
            #cn = data.get('cn')
            #c = data.get('c')
            #s = data.get('s')
            #l = data.get('l')
            #key,cert = create_cert(cn, c, s, l, {})
            #return render(request, 'ca/oneshot_certificate.html', {'key': key, 'cert': cert})
    return render(request, 'routing/create_router.html', {'form': form})