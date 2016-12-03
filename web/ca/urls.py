from django.conf.urls import url, include
from OpenSSL import crypto
from django_ca.views import CertificateRevocationListView
from django_ca.views import OCSPView
from .views import ca_crl, create_certificate

urlpatterns = [
    url(r'^crl/(?P<serial>[0-9A-F:]+)/$',
         CertificateRevocationListView.as_view(
             type=crypto.FILETYPE_PEM,
             digest='sha256',
             content_type='text/plain',
         ),
         name='sha256-crl'),
    url(r'crl/root.ca.thevpn.co.uk/crl.crt',
        ca_crl,
        {
            'digest': 'sha256',
            'serial': 'FF:0E:B8:04:62:C6:41:B2:80:32:FF:FB:75:68:A3:3F',
        },
        name="TheVPN-Root-CA-CRL",
    ),
    url(r'crl/routers.ca.thevpn.co.uk/crl.crt',
        ca_crl,
        {
            'digest': 'sha256',
            'serial': '33:FF:08:18:A8:6C:42:45:95:B1:E7:36:97:79:64:E4',
        },
        name="TheVPN-Routers-CA-CRL",
    ),
    url(r'^ocsp/root.ca.thevpn.co.uk$',
        OCSPView.as_view(
            ca='FF:0E:B8:04:62:C6:41:B2:80:32:FF:FB:75:68:A3:3F',
            expires=600,
            responder_cert='/etc/ssl/oscp-root.ca.thevpn.co.uk.pem',
            responder_key='/etc/ssl/oscp-root.ca.thevpn.co.uk.key',
        )
    ),
    url(r'^ocsp/routers.ca.thevpn.co.uk$',
        OCSPView.as_view(
            ca='33:FF:08:18:A8:6C:42:45:95:B1:E7:36:97:79:64:E4',
            expires=600,
            responder_cert='/etc/ssl/oscp-routers.ca.thevpn.co.uk.pem',
            responder_key='/etc/ssl/oscp-routers.ca.thevpn.co.uk.key',
        )
    ),
    url(r'^certificate/create$',
        create_certificate,
        name="certificate_create"
    ),
]
