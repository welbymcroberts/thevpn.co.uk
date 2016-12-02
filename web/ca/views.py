from django.core.cache import cache
from django.http import HttpResponse
from django.utils.encoding import force_bytes

from django_ca.models import CertificateAuthority
from django_ca.crl import get_crl

from OpenSSL import crypto
def ca_crl(request,serial,digest):
    expires=600
    cache_key = 'crl_%s_%s_%s' %(serial, crypto.FILETYPE_PEM, digest)
    crl = cache.get(cache_key)
    if crl is None:
        ca = CertificateAuthority.objects.prefetch_related('certificate_set').get(serial=serial)
        crl = get_crl(ca, type=crypto.FILETYPE_PEM, expires=expires, digest=force_bytes(digest))
        cache.set(cache_key, crl, expires) 
    return HttpResponse(crl, content_type="text/plain")

