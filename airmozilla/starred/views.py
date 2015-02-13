import json

from django.contrib.auth.models import User
from django import http
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.core.cache import cache
from django.db import transaction
from jsonview.decorators import json_view

from airmozilla.base.mozillians import fetch_user_name
from airmozilla.main.models import Event
from airmozilla.starred.models import StarredEvent, Event


@json_view
def sync_starred_events(request):
    if request.user.is_anonymous():
        ids = []
        return {'ids': []}
    elif request.method == 'POST':
        ids = request.POST.getlist('ids')
        # maybe we do it as a big long string delimited by ,
        # or maybe json. Easier in JQuery?
        #ids = [int(x) for x in ids.split(',')]
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
   # I want to get all starred events for a user
    starred = StarredEvent.objects.filter(user=request.user)
    #events = [star.event for star in starred] #Better way to do this?
    #makes a QuerySet object based on Event
    events = Event.objects.filter(id__in=StarredEvent.objects.filter(
                user=request.user).values('event_id'))
    print events
    #Then you can do things like .filter(other=things).count() etc.
    context['events'] = events
    print context

    return render(request, 'starred/home.html', context)
