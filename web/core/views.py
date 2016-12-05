from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def index(request):
    return render(request, 'core/index.html')

def redirect_if_no_refresh_token(backend, response, social, *args, **kwargs):
    if backend.name == 'google-oauth2' and social and \
       response.get('refresh_token') is None and \
       social.extra_data.get('refresh_token') is None:
        return redirect('/login/google-oauth2?approval_prompt=force')