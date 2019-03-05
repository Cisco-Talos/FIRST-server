from django.urls import path, re_path, include

from . import views

app_name = 'rest'
urlpatterns = [
    re_path(r'test_connection/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.test_connection, name='test_connection'),
    re_path(r'sample/architectures/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.architectures, name='architectures'),
    re_path(r'sample/checkin/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.checkin, name='checkin'),

    #   Metadata related REST URIs
    re_path(r'metadata/history/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_history, name='metadata_history'),
    re_path(r'metadata/applied/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_applied, name='metadata_applied'),
    re_path(r'metadata/unapplied/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_unapplied, name='metadata_unapplied'),
    re_path(r'metadata/get/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_get, name='metadata_get'),
    re_path(r'metadata/delete/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})/(?P<_id>[A-F\d]{26})$',
        views.metadata_delete, name='metadata_delete'),
    re_path(r'metadata/created/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_created, name='metadata_created'),
    re_path(r'metadata/created/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})/(?P<page>\d+)$',
        views.metadata_created, name='metadata_created'),
    re_path(r'metadata/add/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_add, name='metadata_add'),
    re_path(r'metadata/scan/(?P<api_key>[A-F\d]{8}\-(?:[A-F\d]{4}\-){3}[A-F\d]{12})$',
        views.metadata_scan, name='metadata_scan'),

    path(r'status', views.status, name='status'),
]
