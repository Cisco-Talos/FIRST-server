from django.conf.urls import url

from . import views

app_name = 'www'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^profile$', views.profile, name='profile'),

    url(r'^login$', views.login, name='login'),
    url(r'^login/(?P<service>[a-z]+)$', views.login, name='login'),
    url(r'^oauth/(?P<service>[a-z]+)$', views.oauth, name='oauth'),
    url(r'^logout$', views.logout, name='logout'),

    url(r'^register$', views.register, name='register')
]
