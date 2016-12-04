from django.core.cache import cache
from django.http import HttpResponse
from django.utils.encoding import force_bytes
from django import forms
from django.http import Http404
from django.shortcuts import render
from django_ca.models import CertificateAuthority, Certificate
from django_ca.crl import get_crl
from .helpers import create_cert
from OpenSSL import crypto
from django.contrib.auth.decorators import login_required


def ca_crl(request,serial,digest):
    expires=600
    cache_key = 'crl_%s_%s_%s' %(serial, crypto.FILETYPE_PEM, digest)
    crl = cache.get(cache_key)
    if crl is None:
        ca = CertificateAuthority.objects.prefetch_related('certificate_set').get(serial=serial)
        crl = get_crl(ca, type=crypto.FILETYPE_PEM, expires=expires, digest=force_bytes(digest))
        cache.set(cache_key, crl, expires) 
    return HttpResponse(crl, content_type="text/plain")


class CertificateForm(forms.Form):
    cn = forms.CharField(max_length=255,label="DNS of Router (Common Name)",initial="router.at.my.house")
    # TODO: Drop down related to the countries we're using in the ASNs ?
    c = forms.CharField(max_length=2,label="Two Leter Country Code",initial="GB")
    s = forms.CharField(max_length=80,label="State",initial="London")
    l = forms.CharField(max_length=80,label="Locallity",initial="Uxbridge")
    # TODO: SAN?


# TODO: Require admin rights to access this view?
@login_required
def create_certificate(request):
    form = CertificateForm()
    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            cn = data.get('cn')
            c = data.get('c')
            s = data.get('s')
            l = data.get('l')
            key,cert = create_cert(cn, c, s, l, {})
            return render(request, 'ca/oneshot_certificate.html', {'key': key, 'cert': cert})
    return render(request, 'ca/create_certificate.html', {'form': form})


def show_certificate(request, serial=None, cn=None):
    if serial == None and cn == None:
        raise Http404('No Certificate')
    elif serial != None:
        cert = Certificate.objects.get(serial=serial)
    elif cn != None:
        cert = Certificate.objects.get(cn=cn)
    else:
        return HttpResponse(status=500)
    return render(request, 'ca/show_certificate.html', {'cert': cert})


def show_ca(request, cn):
    cert = CertificateAuthority.objects.get(cn=cn)
    return render(request, 'ca/show_certificate.html', {'cert': cert})
