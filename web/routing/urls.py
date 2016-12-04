from django.conf.urls import url, include
from .views import create_router

urlpatterns = [
    url(r'^router/create/?$',
        create_router,
        name='create_router'
    ),
]