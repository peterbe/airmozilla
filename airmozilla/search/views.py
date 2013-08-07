import urllib

from django.shortcuts import render
from django import http

from airmozilla.main.models import Event
from airmozilla.main.views import is_contributor

from funfactory.urlresolvers import reverse

from . import forms
from airmozilla.base.utils import paginate


def home(request):
    context = {}

    if request.GET.get('q'):
        form = forms.SearchForm(request.GET)
    else:
        form = forms.SearchForm()

    if request.GET.get('q') and form.is_valid():
        context['q'] = request.GET.get('q')
        privacy_filter = {}
        privacy_exclude = {}
        if request.user.is_active:
            if is_contributor(request.user):
                privacy_exclude = {'privacy': Event.PRIVACY_COMPANY}
        else:
            privacy_filter = {'privacy': Event.PRIVACY_PUBLIC}

        events = _search(
            request.GET.get('q'),
            privacy_filter=privacy_filter,
            privacy_exclude=privacy_exclude,
            sort=request.GET.get('sort'),
        )
        try:
            page = int(request.GET.get('page', 1))
            if page < 1:
                raise ValueError
        except ValueError:
            return http.HttpResponseBadRequest('Invalid page')
        events_paged = paginate(events, page, 10)
        next_page_url = prev_page_url = None

        def url_maker(page):
            querystring = {'q': context['q'], 'page': page}
            querystring = urllib.urlencode(querystring)
            return '%s?%s' % (reverse('search:home'), querystring)

        if events_paged.has_next():
            next_page_url = url_maker(events_paged.next_page_number())
        if events_paged.has_previous():
            prev_page_url = url_maker(events_paged.previous_page_number())

        context['events_paged'] = events_paged
        context['next_page_url'] = next_page_url
        context['prev_page_url'] = prev_page_url

    else:
        context['events'] = []

    context['form'] = form
    return render(request, 'search/home.html', context)


def _search(q, **options):
    qs = Event.objects.approved()
    # we only want to find upcoming or archived events

    if options.get('privacy_filter'):
        qs = qs.filter(**options['privacy_filter'])
    elif options.get('privacy_exclude'):
        qs = qs.exclude(**options['privacy_exclude'])

    if options.get('sort') == 'date':
        raise NotImplementedError

    sql = """
    (MATCH(title) AGAINST(%s) OR
    MATCH(description,short_description) AGAINST(%s))
    """
    search_escaped = q
    qs = qs.extra(
        where=[sql],
        params=[search_escaped, search_escaped],
        select={
            'score_title': 'match(title) against(%s)',
            'score_desc': 'match(description, short_description) '
                          'against(%s)',
        },
        select_params=[search_escaped, search_escaped],
    )
    qs = qs.order_by('-score_title', '-score_desc')
    return qs
