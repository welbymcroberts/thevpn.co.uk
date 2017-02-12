from django.http import HttpResponse
from django.contrib.auth import logout as authlogout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def whatsmyip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return HttpResponse(ip, content_type="text/plain")

def logout(request):
    authlogout(request)
    return redirect('login')

def redirect_if_no_refresh_token(backend, response, social, *args, **kwargs):
    if backend.name == 'google-oauth2' and social and \
       response.get('refresh_token') is None and \
       social.extra_data.get('refresh_token') is None:
        return redirect('/login/google-oauth2?approval_prompt=force')
