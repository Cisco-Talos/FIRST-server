from django.conf.urls import url

from . import views

app_name = 'rest'
urlpatterns = [
    url(r'^test_connection/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.test_connection, name='test_connection'),
    url(r'^sample/architectures/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.architectures, name='architectures'),
    url(r'^sample/checkin/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.checkin, name='checkin'),

    #   Metadata related REST URIs
    url(r'^metadata/history/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_history, name='metadata_history'),
    url(r'^metadata/applied/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_applied, name='metadata_applied'),
    url(r'^metadata/unapplied/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_unapplied, name='metadata_unapplied'),
    url(r'^metadata/get/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_get, name='metadata_get'),
    #   TODO: migrate to ids with 25 characters
    url(r'^metadata/delete/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})/(?i)(?P<_id>[A-F\d]{24,25})$',
        views.metadata_delete, name='metadata_delete'),
    url(r'^metadata/created/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_created, name='metadata_created'),
    url(r'^metadata/created/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})/(?P<page>\d+)$',
        views.metadata_created, name='metadata_created'),
    url(r'^metadata/add/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_add, name='metadata_add'),
    url(r'^metadata/scan/(?i)(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_scan, name='metadata_scan'),

    url(r'^status$', views.status, name='status'),
]
