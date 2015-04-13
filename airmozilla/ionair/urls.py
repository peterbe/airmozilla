from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(r'channels$',
        views.channels,
        name='channels'),
    url(r'channels/(?P<slug>[\w-]+)$',
        views.channel_events,
        name='channel_events'),
    url(r'events/(?P<slug>[\w-]+)$',
        views.event,
        name='event'),
)
