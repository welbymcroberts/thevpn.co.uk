from django import forms
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse, Http404
from django.utils.encoding import force_bytes
from django.shortcuts import render, redirect
from django_ca.models import CertificateAuthority, Certificate
from django_ca.crl import get_crl
from django_countries import Countries, Regions
from routing.models import Router
from OpenSSL import crypto
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout,Field,Submit,HTML
from crispy_forms.bootstrap import FormActions
from .helpers import create_cert, get_duplicates_by_cn

class CertificateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CertificateForm, self).__init__(*args, **kwargs)
        helper = self.helper = FormHelper(self)
    
        layout = helper.layout = Layout()
        for field_name, field in self.fields.items():
            if isinstance(field, forms.CharField) and field.initial is not None:
                layout.append(Field(field_name, placeholder=field.initial ))
                field.initial = ""
            else:
                layout.append(Field(field_name))
                
        layout.append(FormActions(
            Submit('submit', 'Create', css_class="btn btn-primary pull-right"),
            HTML('<a href="javascript:history.go(-1)" class="btn btn-info">Cancel</a>'),
            ))
    
    def clean(self):
        super(CertificateForm, self).clean()
        if 'cn' in self.cleaned_data:
            try:
                exists = Certificate.objects.filter(cn=self.cleaned_data['cn'], revoked=False)[:1].get()
            except:
                exists = False
            
            if exists:
                self._errors['cn'] = [u'A certificate with this CN already exists, please revoke that certificate first.']
        return self.cleaned_data

    cn = forms.CharField(max_length=255,label="DNS of Router (Common Name)",initial="router.at.my.house")
    c = forms.ChoiceField(label="Country", choices=Countries,initial="GB")
    
    s = forms.CharField(max_length=80,label="State",initial="London")
    l = forms.CharField(max_length=80,label="Locallity",initial="Uxbridge")
    # TODO: SAN?

class RevokeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(RevokeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
    
    reason = forms.ChoiceField(label="Revoke Reason", choices=Certificate.REVOCATION_REASONS)

# for admins only?
@login_required
def ca_crl(request,serial,digest):
    expires=600
    cache_key = 'crl_%s_%s_%s' %(serial, crypto.FILETYPE_PEM, digest)
    crl = cache.get(cache_key)
    if crl is None:
        ca = CertificateAuthority.objects.prefetch_related('certificate_set').get(serial=serial)
        crl = get_crl(ca, type=crypto.FILETYPE_PEM, expires=expires, digest=force_bytes(digest))
        cache.set(cache_key, crl, expires) 
    return HttpResponse(crl, content_type="text/plain")

@staff_member_required
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
            key,cert = create_cert(cn, c, s, l, {data.get('cn'), })
            return render(request, 'ca/oneshot_certificate.html', {'key': key, 'cert': cert.pub})
    return render(request, 'ca/create_certificate.html', {'form': form})

@staff_member_required
def list_certificates(request, type=None ):
    type = "all" if type is None or type == "" else type
    
    linkedCerts = activeCerts = revokedCerts = uniqueCerts = None
    if type == "all" or type == "active":
        linkedCerts = Certificate.objects.filter(router__certificate__isnull=False).order_by('router__owner','cn').all()
        for cert in linkedCerts:
            cert.routers = Router.objects.filter(certificate=cert)
    
    if type == "all" or type == "valid":
        activeCerts = Certificate.objects.filter(router__certificate=None).exclude(revoked=True).order_by('cn').all()
    
    if type == "all" or type == "revoked":
        revokedCerts = Certificate.objects.filter(router__certificate=None, revoked=True).order_by('revoked_date', 'cn').all()
    
    if type == "duplicate":
        uniqueCerts = Certificate.objects.values('cn').annotate(count=Count('cn')).filter(count__gt=1).order_by('-count')
        for cert in uniqueCerts:
            try:
                tmp_cert = Certificate.objects.filter(cn=cert['cn'],revoked=False)[:1].get()
            except:
                tmp_cert = Certificate.objects.filter(cn=cert['cn']).order_by('revoked_date')[:1].get()
                    
            cert['serial'] = tmp_cert.serial
            cert['expires'] = tmp_cert.expires
               
        
    return render(request, 'ca/list_certificates.html', {'linkedCerts': linkedCerts, 'activeCerts': activeCerts, 'revokedCerts': revokedCerts, 'uniqueCerts': uniqueCerts})

@login_required
def show_certificate(request, serial=None, cn=None):
    if serial == None and cn == None:
        raise Http404('No Certificate')
    elif serial != None:
        cert = Certificate.objects.get(serial=serial)
    elif cn != None:
        cert = Certificate.objects.filter(cn=cn).first()
    else:
        return HttpResponse(status=500)
    
    format = request.GET.get('format')
    if format == 'pem':
        response = HttpResponse(content=cert.pub, content_type="text/plain")
        response['Filename'] = cert.cn + '.pem'
        response['Content-Disposition'] = 'attachment; filename="' + cert.cn + '.pem"'
        return response

    duplicateCerts = Certificate.objects.filter(cn=cert.cn).exclude(id=cert.id)
    
    if cert.revoked is None or cert.revoked == False:
        cert.revoked_date = "No"
    
    revokeForm = None
    if not cert.revoked and request.user.is_active and request.user.is_staff:
        revokeForm = RevokeForm()
    
    return render(request, 'ca/show_certificate.html', {'cert': cert, 'duplicateCerts': get_duplicates_by_cn(cert), 'revokeForm': revokeForm})

@login_required
def show_certificate_authority(request, cn):
    cert = CertificateAuthority.objects.get(cn=cn)
    
    try:
        if cert.revoked is None or cert.revoked is "":
            cert.revoked = ""
            cert.revoked_date = "No"
    except:
        cert.revoked = ""
        cert.revoked_date = "No"

    return render(request, 'ca/show_certificate.html', {'cert': cert, 'canRevoke' : False})

@staff_member_required
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
                cert.revoke(reason=reason)
                messages.add_message(request, messages.SUCCESS, 'This certificate has been revoked')

        return redirect('/ca/certificate/show/%s' % serial)
        
        
        