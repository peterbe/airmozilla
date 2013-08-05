from django.shortcuts import render

from airmozilla.main.models import Event
from airmozilla.main.views import is_contributor

from . import forms


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

        context['events'] = _search(
            request.GET.get('q'),
            privacy_filter=privacy_filter,
            privacy_exclude=privacy_exclude,
            sort=request.GET.get('sort'),
        )
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
