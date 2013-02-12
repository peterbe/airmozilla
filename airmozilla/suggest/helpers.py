from jingo import register
from funfactory.urlresolvers import reverse


_STATES = [
    {
        'required': ['submitted'],
        'view': 'suggest:summary',
        'description': 'Submitted'
    },
    {
        'required': ['description'],
        'view': 'suggest:description',
        'description': 'No description entered'
    },
    {
        'required': ['start_time', 'location', 'privacy'],
        'view': 'suggest:details',
        'description': 'Details missing',
    },
    {
        'required': ['placeholder_img'],
        'view': 'suggest:placeholder',
        'description': 'No placeholder image',
    },
    {
        'required': [lambda event: event.participants.all().count()],
        'view': 'suggest:participants',
        'description': 'No participants selected'
    },
]


def _get_state(event):
    for state in _STATES:
        if state.get('required'):
            all = True
            for must in state['required']:
                if isinstance(must, basestring):
                    if not getattr(event, must, None):
                        all = False
                else:
                    if not must(event):
                        all = False
            if all:
                return state


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
