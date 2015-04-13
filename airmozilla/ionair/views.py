import functools

from django.shortcuts import get_object_or_404
from jsonview.decorators import json_view

from airmozilla.main.models import Event, Channel


def add_CORS_header(f):
    @functools.wraps(f)
    def wrapper(request, *args, **kw):
        response = f(request, *args, **kw)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    return wrapper


@add_CORS_header
@json_view
def channels(request):
    all = []
    for channel in Channel.objects.filter(parent__isnull=True):
        all.append({
            'name': channel.name,
            'slug': channel.slug,
        })
    return {'results': all}


@add_CORS_header
@json_view
def channel_events(request, slug):
    all = []
    _channels = Channel.objects.filter(slug=slug)
    _events = (
        Event.objects.archived()
        .filter(channels=_channels)
        .order_by('-start_time')
    )
    for e in _events:
        all.append({
            'title': e.title,
            'slug': e.slug,
            'start_time': e.start_time,
        })
    return {'results': all}


@add_CORS_header
@json_view
def event(request, slug):
    e = get_object_or_404(Event, slug=slug)
    mp4_url = 'https://vid.ly/{tag}?content=video&format=mp4'
    mp4_url = 'http://cf.cdn.vid.ly/{tag}/iphone_stream4.m3u8'
    mp4_url = mp4_url.format(
        tag=e.template_environment['tag']
    )
    _event = {
        'title': e.title,
        'description': e.description,
        'mp4_url': mp4_url,
    }
    return {'result': _event}
