import json
import collections

from django.contrib.auth.models import User
#from django import http
from django.shortcuts import get_object_or_404, render, redirect
#from django.template.loader import render_to_string
#from django.core.cache import cache
#from django.db import transaction
from jsonview.decorators import json_view

#from airmozilla.base.mozillians import fetch_user_name
from airmozilla.starred.models import StarredEvent, Event
from airmozilla.main.models import (
    Event,
    CuratedGroup,
)


@json_view
def sync_starred_events(request):
    if request.user.is_anonymous():
        ids = []
        return {'ids': []}
    elif request.method == 'POST':
        ids = request.POST.getlist('ids')
        StarredEvent.objects.filter(user=request.user).exclude(
            id__in=ids).delete()
        for id in ids:
            try:
                event = Event.objects.get(id=id)
                StarredEvent.objects.get_or_create(
                    user=request.user,
                    event=event
                )
            except Event.DoesNotExist:
                # ignore events that don't exist but fail on other errors
                pass
    

    starred = StarredEvent.objects.filter(user=request.user)
    ids = list(starred.values_list('event_id', flat=True))
    return {'ids': ids}


def home(request):
    context = {}

    events = Event.objects.filter(id__in=StarredEvent.objects.filter(
                user=request.user).values('event_id'))

    curated_groups_map = collections.defaultdict(list)
    curated_groups = (
        CuratedGroup.objects.all()
        .values_list('event_id', 'name')
        .order_by('name')
    )
    for event_id, name in curated_groups:
        curated_groups_map[event_id].append(name)

    def get_curated_groups(event):
        return curated_groups_map.get(event.id)

    context= {
        'events': events,
        'get_curated_groups': get_curated_groups,
    }

    return render(request, 'starred/home.html', context)
