import collections

from django.shortcuts import render
from django.views.decorators import cache
from session_csrf import anonymous_csrf

from jsonview.decorators import json_view
from funfactory.urlresolvers import reverse

from airmozilla.base.utils import paginate
from airmozilla.starred.models import StarredEvent, Event
from airmozilla.main.models import (
    Event,
    CuratedGroup,
)


@cache.cache_control(private=True)
@anonymous_csrf
@json_view
def sync_starred_events(request):
    context = {'csrf_token': request.csrf_token}
    if request.user.is_anonymous():
        context['ids'] = []
        return context
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
    context['ids'] = list(starred.values_list('event_id', flat=True))
    return context


def home(request, page=1):
    context = {}
    events = False

    if (request.user.is_authenticated()):
        ## LOGGED IN USER VIEW
        events = (
            Event.objects.filter(starredevent__user=request.user.id)
            .order_by('-created')
        )
        # END
    elif request.method == 'POST':
        # ANONYMOUS JAVASCRIPT POST
        ids = request.GET.getlist('ids')
        events = Event.objects.filter(id__in=ids)
        # END

    starred_paged = next_page_url = prev_page_url = None
    if events:
        starred_paged = paginate(events, page, 10)

        # to simplify the complexity of the template when it tries to make the
        # pagination URLs, we just figure it all out here
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
                x.id for x in starred_paged
            ])
            .values_list('event_id', 'name')
            .order_by('name')
        )
        for event_id, name in curated_groups:
            curated_groups_map[event_id].append(name)

    def get_curated_groups(event):
        if events:
            return curated_groups_map.get(event.id)

    context = {
        'events': starred_paged,
        'get_curated_groups': get_curated_groups,
        'next_page_url': next_page_url,
        'prev_page_url': prev_page_url,
    }

    if (request.method == 'POST' and not request.user.id):
        ## ANONYMOUS JAVASCRIPT POST
        return render(request, 'starred/events.html', context)
    else:
        ## LOGGED IN USER
        return render(request, 'starred/home.html', context)
    # END

