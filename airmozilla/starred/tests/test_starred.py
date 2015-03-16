import json

from airmozilla.base.tests.testbase import DjangoTestCase
from funfactory.urlresolvers import reverse
from nose.tools import eq_, ok_
from airmozilla.main.models import Event
from airmozilla.starred.models import (
    StarredEvent,
)


class TestStarredEvent(DjangoTestCase):
    fixtures = ['airmozilla/manage/tests/main_testdata.json']

    def setUp(self):
        super(TestStarredEvent, self).setUp()

        # create the url
        self.url = reverse('starred:sync')
        # so, let's sign in
        self.user =  self._login(username='lisa')

    def create_event(self, title):
        # instantiate test event
        event = Event.objects.get(title='Test event')
        event_count = Event.objects.count()

        # create more events
        return Event.objects.create(
            title=title,
            slug='event' + str(event_count),
            description=event.description,
            start_time=event.start_time,
            privacy=Event.PRIVACY_PUBLIC,
            placeholder_img=event.placeholder_img,
            location=event.location,
        )

    def test_sync_starred_events(self):

        url = self.url
        event1 = Event.objects.get(title='Test event')

        # pass url to the browser
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # get the empty list of event ids in json format
        structure = json.loads(response.content)
        csrf_token = structure['csrf_token']
        eq_(structure, {'csrf_token': csrf_token, "ids": []})

        # add an event id to the list
        structure['ids'].append(event1.id)
        # send synced list to browser
        response = self.client.post(url, {'ids': structure['ids']})
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {'csrf_token': csrf_token, "ids": [event1.id]})

    def test_removed_starred_event(self):
        url = self.url
        event1 = Event.objects.get(title='Test event')
        event2 = self.create_event('Test event 2')

        StarredEvent.objects.create(user=self.user, event=event1)
        StarredEvent.objects.create(user=self.user, event=event2)

        response = self.client.post(url, {'ids': [event1.id]})
        eq_(response.status_code, 200)

        ok_(StarredEvent.objects.filter(event=event1.id))
        ok_(not StarredEvent.objects.filter(event=event2.id))

    def test_invalid_starred_event_id(self):

        url = self.url
        event1 = Event.objects.get(title='Test event')

        # pass url to the browser
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # get the empty list of event ids in json format
        structure = json.loads(response.content)
        csrf_token = structure['csrf_token']
        eq_(structure, {'csrf_token': csrf_token, "ids": []})

        # add event id to the list
        structure['ids'].append(event1.id)
        # send list to the browser
        response = self.client.post(url, {'ids': structure['ids']})
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {'csrf_token': csrf_token, "ids": [event1.id]})

        # delete event
        event1.delete()
        # send updated list to the browser
        response = self.client.post(url, {'ids': structure['ids']})
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {'csrf_token': csrf_token, "ids": []})

    def test_anonymous_user(self):
        # log out user from setUp()
        self.client.logout()

        url = self.url

        send = {'ids': [23, 24]}

        # send list to the browser
        response = self.client.post(url, send)
        receive = json.loads(response.content)
        csrf_token = receive['csrf_token']
        # verify the list is returned to the user
        eq_(receive, {'csrf_token': csrf_token, 'ids': []})
