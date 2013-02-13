from django import http
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from funfactory.urlresolvers import reverse
from airmozilla.main.models import SuggestedEvent
from . import forms


@login_required
def start(request):
    data = {}
    if request.method == 'POST':
        form = forms.StartForm(request.POST)
        if form.is_valid():
            event = SuggestedEvent.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                slug=form.cleaned_data['slug'],
            )
            url = reverse('suggest:description', args=(event.pk,))
            return redirect(url)
    else:
        form = forms.StartForm()

        data['suggestions'] = (
            SuggestedEvent.objects
            .filter(user=request.user)
            .order_by('modified')
        )
    data['form'] = form

    return render(request, 'suggest/start.html', data)


@login_required
def description(request, id):
    event = get_object_or_404(SuggestedEvent, pk=id)
    if event.user != request.user:
        return http.HttpResponseBadRequest('Not your event')

    if request.method == 'POST':
        form = forms.DescriptionForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            url = reverse('suggest:details', args=(event.pk,))
            return redirect(url)
    else:
        form = forms.DescriptionForm(instance=event)

    return render(request, 'suggest/description.html', {'form': form})


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
            url = reverse('suggest:placeholder', args=(event.pk,))
            return redirect(url)
    else:
        form = forms.DetailsForm(instance=event)

    return render(request, 'suggest/details.html', {'form': form})


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
            url = reverse('suggest:participants', args=(event.pk,))
            return redirect(url)
    else:
        form = forms.PlaceholderForm()

    return render(request, 'suggest/placeholder.html', {'form': form})


@login_required
def participants(request, id):
    event = get_object_or_404(SuggestedEvent, pk=id)
    if event.user != request.user:
        return http.HttpResponseBadRequest('Not your event')

    form_class = forms.ParticipantsForm
    if request.method == 'POST':
        form = form_class(request.POST, instance=event)
        if form.is_valid():
            event = form.save()
            form.save_m2m()
            url = reverse('suggest:submit', args=(event.pk,))
            return redirect(url)
    else:
        form = form_class(instance=event)

    return render(request, 'suggest/participants.html', {'form': form})


@login_required
def summary(request, id):
    event = get_object_or_404(SuggestedEvent, pk=id)
    if event.user != request.user:
        return http.HttpResponseBadRequest('Not your event')

    return render(request, 'suggest/summary.html', {'event': event})
