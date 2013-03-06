from django.conf.urls.defaults import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.start, name='start'),
    url(r'^(?P<id>\d+)/description/$', views.description, name='description'),
    url(r'^(?P<id>\d+)/details/$', views.details, name='details'),
    url(r'^(?P<id>\d+)/image/$', views.placeholder, name='placeholder'),
    url(r'^(?P<id>\d+)/participants/$', views.participants,
        name='participants'),
    url(r'^(?P<id>\d+)/summary/$', views.summary, name='summary'),
)
