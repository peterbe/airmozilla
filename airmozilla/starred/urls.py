from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.starred_events, name='starred_events'),
    url(r'^sync$', views.sync_starred_events, name='sync_starred_events'),
)
