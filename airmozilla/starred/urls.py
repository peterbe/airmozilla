from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.home, name='home'),
    url(r'^sync/$', views.sync_starred_events, name='sync_starred_events'),
)
