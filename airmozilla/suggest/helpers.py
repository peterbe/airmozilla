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
    {
        'not': [lambda event: event.participants.all().count()],
        'view': 'suggest:participants',
        'description': 'No participants selected'
    },
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
