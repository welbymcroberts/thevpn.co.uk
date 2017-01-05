from OpenSSL import crypto
import datetime
from django.conf import settings
from django_ca.models import Certificate, CertificateAuthority
import datetime


def create_key():
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA,2048)
    return crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)


def create_csr(csr,key):
    san_list = []
    for san in csr['san']:
        san_list.append("DNS:%s" %san)
    pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, key)
    req = crypto.X509Req()
    req.set_pubkey(pkey)
    req.set_version(2)
    req.add_extensions([crypto.X509Extension(b"subjectAltName", False, bytes(", ".join(san_list), 'utf-8')),
                        crypto.X509Extension(b'basicConstraints', False, b'CA:FALSE')])
    subj = req.get_subject()
    subj.CN = csr['CN']
    subj.C = csr['C']
    subj.ST = csr['S']
    subj.L = csr['L']
    subj.O = settings.THEVPN_NAME
    req.sign(pkey, "sha256")
    return crypto.dump_certificate_request(crypto.FILETYPE_PEM, req)


def sign_csr(csr,ca_cn,attrib,algorithm='sha512',expires=1825):
    ca = CertificateAuthority.objects.get(cn=ca_cn)
    # TODO: Check to see if the certificate already exists, and if so, is it the same user? Revoke the old one?
    cert = Certificate(ca=ca, csr=csr)
    expiry = datetime.datetime.now() + datetime.timedelta(expires)
    cert.x509 = Certificate.objects.init(
            ca=ca, csr=csr, algorithm=algorithm, expires=expiry, subject={'CN': attrib.get('CN'), },
            subjectAltName=attrib['san'])
    cert.save()
    return cert.pub


def create_cert(cn, c, s, l, san, ca_cn=None):
    if ca_cn is None: ca_cn = 'routers.ca.' + settings.THEVPN_FQDN;
    key = create_key()
    attrib = {'CN': cn, 'C': c, 'S': s, 'L': l, 'san': san}
    csr = create_csr(csr=attrib, key=key)
    cert = sign_csr(csr, ca_cn, attrib)
    return key, cert
