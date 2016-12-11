from django.conf.urls import url, include
from .views import create_router, peer_list

urlpatterns = [
    url(r'^router/create/?$',
        create_router,
        name='create_router'
    ),
    url(r'^peers/(?P<endpointkey>\w+)/?$',
        peer_list,
        name='peer_list'
    ),
]