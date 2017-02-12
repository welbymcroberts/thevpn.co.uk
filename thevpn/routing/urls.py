from django.conf.urls import url, include
from .views import create_router, delete_router, show_certificate, \
    activate_certificate, revoke_certificate, request_certificate, router_script, graph, peer_list, ping

urlpatterns = [
    url(r'^router/create/$',
        create_router,
        name='create_router'
    ),
    url(r'^router/delete/(?P<endpointkey>\w+)/$',
        delete_router,
        name='delete_router'
    ),
    url(r'^certificate/show/(?P<endpointkey>\w+)$',
        show_certificate,
        name='show_certificate'
    ),
    url(r'^certificate/show/(?P<serial>([0-9A-Za-z]{2}:){15}[0-9A-Za-z]{2})$',
        show_certificate,
        name='show_certificate'
    ),
    url(r'^certificate/activate/(?P<serial>([0-9A-Za-z]{2}:){15}[0-9A-Za-z]{2})$',
        activate_certificate,
        name="certificate_activate"
    ),
    url(r'^certificate/revoke/(?P<serial>([0-9A-Za-z]{2}:){15}[0-9A-Za-z]{2})$',
        revoke_certificate,
        name="certificate_revoke"
    ),
    url(r'^certificate/request/(?P<endpointkey>\w+)$',
        request_certificate,
        name='request_certificate'
    ),
    url(r'^script/(?P<endpointkey>\w+)/?$',
        router_script,
        name='router_script'
    ),
    url(r'^graph/(?P<type>\w+)/?$',
        graph,
        name='graph_peer'
    ),
    url(r'^peers/(?P<endpointkey>\w+)/?$',
        peer_list,
        name='peer_list'
    ),
    url(r'^ping/(?P<endpointkey>\w+)/$',
        ping,
        name='ping'
    ),
]