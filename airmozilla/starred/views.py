from django.contrib.auth.models import User
from django import http
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.db.models import Q, Max
from django.core.cache import cache
from django.db import transaction
from django.views.decorators.http import require_POST
from jsonview.decorators import json_view

from airmozilla.main.models import Event
from .models import StarredEvents
from airmozilla.base.mozillians import fetch_user_name


@json_view
def sync_starred_events(request):
    if request.method == 'POST':
        ids = request.POST['ids']
        # maybe we do it as a big long string delimited by ,
        # or maybe json. Easier in JQuery?
        #ids = [int(x) for x in ids.split(',')]
        StarredEvents.objects.filter(user=request.user).exclude(
            id__in=ids).delete()
        for id in ids:
            event = Event.objects.get(id=id)
            StarredEvents.objects.get_or_create(user=request.user, event=event)
        return True

    else:
        starred = StarredEvents.objects.filter(user=request.user)
        ids = [star.event.id for star in starred] #Better way to do this?
        return {'ids': ids}


def home(request):
    context = {}
   # I want to get all starred events for a user
    starred = StarredEvents.objects.filter(user=request.user)
    #events = [star.event for star in starred] #Better way to do this?
    events = Event.objects.filter(id__in=StarredEvents.objects.filter(
                user=request.user).values('event_id'))
    context['events'] = events

    return render(request, 'starred/starred.html', context)
