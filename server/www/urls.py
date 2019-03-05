from django.urls import path, re_path, include

from . import views

app_name = 'www'
urlpatterns = [
    path(r'', views.index, name='index'),
    path(r'profile', views.profile, name='profile'),

    path(r'login', views.login, name='login'),
    re_path(r'^login/(?P<service>[a-z]+)$', views.login, name='login'),
    re_path(r'^oauth/(?P<service>[a-z]+)$', views.oauth, name='oauth'),
    path(r'logout', views.logout, name='logout'),

    path(r'register', views.register, name='register')
]
