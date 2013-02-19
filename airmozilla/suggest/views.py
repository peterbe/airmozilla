import datetime
from django import http
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import slugify

from funfactory.urlresolvers import reverse
from airmozilla.main.models import SuggestedEvent, Event
from . import forms


def _increment_slug_if_exists(slug):
    base = slug
    count = 0
    while Event.objects.filter(slug__iexact=slug):
        if not count:
            # add the date
            now = datetime.datetime.utcnow()
            slug = base = slug + now.strftime('-%Y%m%d')
            count = 2
        else:
            slug = base + '-%s' % count
            count += 1
    return slug


@login_required
def start(request):
    data = {}
    if request.method == 'POST':
        form = forms.StartForm(request.POST, user=request.user)
        if form.is_valid():
            slug = slugify(form.cleaned_data['title'])
            slug = _increment_slug_if_exists(slug)
            event = SuggestedEvent.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                slug=slug,
            )
            # XXX use next_url() instead?
            url = reverse('suggest:description', args=(event.pk,))
            return redirect(url)
    else:
        form = forms.StartForm(user=request.user)

        data['suggestions'] = (
            SuggestedEvent.objects
            .filter(user=request.user)
            .order_by('modified')
        )
    data['form'] = form

    return render(request, 'suggest/start.html', data)


@login_required
def title(request, id):
    event = get_object_or_404(SuggestedEvent, pk=id)
    if event.user != request.user:
        return http.HttpResponseBadRequest('Not your event')

    if request.method == 'POST':
        form = forms.TitleForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            # XXX use next_url() instead?
            url = reverse('suggest:description', args=(event.pk,))
            return redirect(url)
    else:
        form = forms.TitleForm(instance=event)

    data = {'form': form, 'event': event}
    return render(request, 'suggest/title.html', data)


@login_required
def description(request, id):
    event = get_object_or_404(SuggestedEvent, pk=id)
    if event.user != request.user:
        return http.HttpResponseBadRequest('Not your event')

    if request.method == 'POST':
        form = forms.DescriptionForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            # XXX use next_url() instead?
            url = reverse('suggest:details', args=(event.pk,))
            return redirect(url)
    else:
        form = forms.DescriptionForm(instance=event)

    data = {'form': form, 'event': event}
    return render(request, 'suggest/description.html', data)


@login_required
def details(request, id):
    event = get_object_or_404(SuggestedEvent, pk=id)
    if event.user != request.user:
        return http.HttpResponseBadRequest('Not your event')

    if request.method == 'POST':
        form = forms.DetailsForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.save()
            form.save_m2m()
            # XXX use next_url() instead?
            url = reverse('suggest:placeholder', args=(event.pk,))
            return redirect(url)
    else:
        form = forms.DetailsForm(instance=event)

    data = {'form': form, 'event': event}
    return render(request, 'suggest/details.html', data)


@login_required
def placeholder(request, id):
    event = get_object_or_404(SuggestedEvent, pk=id)
    if event.user != request.user:
        return http.HttpResponseBadRequest('Not your event')

    if request.method == 'POST':
        form = forms.PlaceholderForm(
            request.POST,
            request.FILES,
            instance=event
        )
        if form.is_valid():
            event = form.save()
            # XXX use next_url() instead?
            url = reverse('suggest:summary', args=(event.pk,))
            return redirect(url)
    else:
        form = forms.PlaceholderForm()

    data = {'form': form, 'event': event}
    return render(request, 'suggest/placeholder.html', data)


#@login_required
#def participants(request, id):
#    event = get_object_or_404(SuggestedEvent, pk=id)
#    if event.user != request.user:
#        return http.HttpResponseBadRequest('Not your event')
#
#    form_class = forms.ParticipantsForm
#    if request.method == 'POST':
#        form = form_class(request.POST, instance=event)
#        if form.is_valid():
#            event = form.save()
#            form.save_m2m()
#            url = reverse('suggest:submit', args=(event.pk,))
#            return redirect(url)
#    else:
#        form = form_class(instance=event)
#
#    return render(request, 'suggest/participants.html', {'form': form})


@login_required
def summary(request, id):
    event = get_object_or_404(SuggestedEvent, pk=id)
    if event.user != request.user:
        return http.HttpResponseBadRequest('Not your event')

    return render(request, 'suggest/summary.html', {'event': event})
