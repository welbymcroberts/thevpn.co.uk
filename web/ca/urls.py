from django.conf import settings
from django.conf.urls import url, include
from OpenSSL import crypto
from django_ca.views import CertificateRevocationListView
from django_ca.views import OCSPView
from .views import ca_crl, create_certificate, show_certificate, show_ca

urlpatterns = [
    url(r'^crl/(?P<serial>[0-9A-F:]+)/$',
         CertificateRevocationListView.as_view(
             type=crypto.FILETYPE_PEM,
             digest='sha256',
             content_type='text/plain',
         ),
         name='sha256-crl'),
    url(r'crl/root.ca.' + settings.THEVPN_FQDN + '/crl.crt',
        ca_crl,
        {
            'digest': 'sha256',
            'serial': 'D4:6D:66:35:03:11:47:A3:B4:23:F2:A4:21:39:45:F8',
        },
        name="TheVPN-Root-CA-CRL",
    ),
    url(r'crl/routers.ca.' + settings.THEVPN_FQDN + '/crl.crt',
        ca_crl,
        {
            'digest': 'sha256',
            'serial': '6E:A9:4B:83:8D:FE:40:53:BA:0A:7E:AB:CD:80:B0:86',
        },
        name="TheVPN-Routers-CA-CRL",
    ),
    url(r'^ocsp/root.ca.' + settings.THEVPN_FQDN + '$',
        OCSPView.as_view(
            ca='D4:6D:66:35:03:11:47:A3:B4:23:F2:A4:21:39:45:F8',
            expires=600,
            responder_cert='/etc/ssl/oscp-root.ca.' + settings.THEVPN_FQDN + '.pem',
            responder_key='/etc/ssl/oscp-root.ca.' + settings.THEVPN_FQDN + '.key',
        )
    ),
    url(r'^ocsp/routers.ca.' + settings.THEVPN_FQDN + '$',
        OCSPView.as_view(
            ca='6E:A9:4B:83:8D:FE:40:53:BA:0A:7E:AB:CD:80:B0:86',
            expires=600,
            responder_cert='/etc/ssl/oscp-routers.ca.' + settings.THEVPN_FQDN + '.pem',
            responder_key='/etc/ssl/oscp-routers.ca.' + settings.THEVPN_FQDN + '.key',
        )
    ),
    url(r'^certificate/create$',
        create_certificate,
        name="certificate_create"
    ),
    url(r'^certificate/show/root.ca.' + settings.THEVPN_FQDN + '/?$',
        show_ca,
        {
            "cn": "root.ca." + settings.THEVPN_FQDN + "",
        },
        name="certificate_show_root"
    ),
    url(r'^certificate/show/routers.ca.' + settings.THEVPN_FQDN + '/?$',
        show_ca,
        {
            "cn": "routers.ca." + settings.THEVPN_FQDN + "",
        },
        name="certificate_show_root"
    ),
    url(r'^certificate/show/(?P<serial>([0-9A-Za-z]{2}:){15}[0-9A-Za-z]{2})/?$',
        show_certificate,
        name="certificate_show"
    ),
    url(r'^certificate/show/(?P<cn>((\w+).+)(\w+))/?$',
        show_certificate,
        name="certificate_show"
    )
]
