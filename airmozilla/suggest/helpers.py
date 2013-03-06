from jingo import register
from funfactory.urlresolvers import reverse


_STATES = [
    {
        'required': ['submitted'],
        'view': 'suggest:summary',
        'description': 'Submitted'
    },
    {
        'not': ['description'],
        'view': 'suggest:description',
        'description': 'Description not entered'
    },
    {
        'not': ['start_time', 'location', 'privacy'],
        'view': 'suggest:details',
        'description': 'Details missing',
    },
    {
        'not': ['placeholder_img'],
        'view': 'suggest:placeholder',
        'description': 'No placeholder image',
    },
    #{
    #    'not': [lambda event: event.participants.all().count()],
    #    'view': 'suggest:participants',
    #    'description': 'No participants selected'
    #},
]

_DEFAULT_STATE = {
    'view': 'suggest:summary',
    'description': 'Not yet submitted',
}


def _get_state(event):
    for state in _STATES:
        if state.get('required'):
            requirements = state['required']
        else:
            requirements = state['not']
        all = True
        for requirement in requirements:
            if isinstance(requirement, basestring):
                if not getattr(event, requirement, None):
                    all = False
            else:
                if not requirement(event):
                    all = False
        if state.get('required'):
            if all:
                return state
        else:
            if not all:
                return state
    return _DEFAULT_STATE


@register.function
def next_url(event):
    state = _get_state(event)
    assert state, event
    return reverse(state['view'], args=(event.pk,))


@register.function
def state_description(event):
    state = _get_state(event)
    assert state, event
    return state['description']


@register.function
def breadcrumbs(event):
    state = _get_state(event)
    links = []
    # start
    links.append({
        'url': reverse('suggest:start'),
        'description': 'Start',
        'available': True,
    })

    # title
    links.append({
        'url': reverse('suggest:title', args=(event.pk,)),
        'description': 'Title',
        'available': True,
    })

    available = state['view'] != 'suggest:description'
    # description
    links.append({
        'url': reverse('suggest:description', args=(event.pk,)),
        'description': 'Description',
        'available': available,
    })

    # details
    if available:
        available = state['view'] != 'suggest:details'
    links.append({
        'url': reverse('suggest:details', args=(event.pk,)),
        'description': 'Details',
        'available': available,
    })

    # placeholder
    if available:
        available = state['view'] != 'suggest:placeholder'
    links.append({
        'url': reverse('suggest:placeholder', args=(event.pk,)),
        'description': 'Placeholder',
        'available': available,
    })

    # summary
    if available:
        available = state['view'] != 'suggest:summary'
    links.append({
        'url': reverse('suggest:summary', args=(event.pk,)),
        'description': 'Summary',
        'available': available,
    })

    return links
