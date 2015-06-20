import requests

from django.shortcuts import get_object_or_404

from jsonview.decorators import json_view

from airmozilla.main.helpers import thumbnail
from airmozilla.main.models import Event, VidlySubmission


@json_view
def event_meta_data(request):
    slug = request.GET.get('slug')
    event = get_object_or_404(Event, slug=slug)

    image = event.picture and event.picture.file or event.placeholder_img
    geometry = '160x90'
    crop = 'center'

    thumb = thumbnail(image, geometry, crop=crop)
    video_url = None

    if event.template and 'vid.ly' in event.template.name.lower():
        tag = event.template_environment['tag']

        video_format = 'webm'

        for submission in VidlySubmission.objects.filter(event=event, tag=tag):
            if submission.hd:
                video_format = 'hd_webm'

        video_url = 'https://vid.ly/{0}?content=video&format={1}'.format(
            tag, video_format
        )

    headers = {
        'User-Agent': request.META.get('HTTP_USER_AGENT')
    }

    r = requests.head(video_url, headers=headers)

    return {
        'title': event.title,
        'status': event.status,
        'description': event.description,
        'preview_img': thumb.url,
        'video_url': r.headers['location'],
    }

