import json
import collections

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect

from jsonview.decorators import json_view
from funfactory.urlresolvers import reverse

from airmozilla.base.utils import paginate
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


def home(request, page=1):
    context = {}

    starred_events_qs = (
        StarredEvent.objects.filter(user=request.user)
        .select_related('event')
        .order_by('-created')
    )
    starred_paged = paginate(starred_events_qs, page, 10)

    # to simplify the complexity of the template when it tries to make the
    # pagination URLs, we just figure it all out here
    next_page_url = prev_page_url = None
    if starred_paged.has_next():
        next_page_url = reverse(
            'starred:home',
            args=(starred_paged.next_page_number(),)
        )
    if starred_paged.has_previous():
        prev_page_url = reverse(
            'starred:home',
            args=(starred_paged.previous_page_number(),)
        )

    curated_groups_map = collections.defaultdict(list)
    curated_groups = (
        CuratedGroup.objects.filter(event__in=[
            x.event.id for x in starred_paged
        ])
        .values_list('event_id', 'name')
        .order_by('name')
    )
    for event_id, name in curated_groups:
        curated_groups_map[event_id].append(name)

    def get_curated_groups(event):
        return curated_groups_map.get(event.id)

    context= {
        'starred': starred_paged,
        'get_curated_groups': get_curated_groups,
        'next_page_url': next_page_url,
        'prev_page_url': prev_page_url,
    }

    return render(request, 'starred/home.html', context)
