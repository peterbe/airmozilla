import json

from airmozilla.base.tests.testbase import DjangoTestCase
from django.contrib.auth.models import User

from funfactory.urlresolvers import reverse
from nose.tools import eq_, ok_

from airmozilla.main.models import Event
from airmozilla.starred.models import (
    StarredEvents,
)


class TestStarredEvent(DjangoTestCase):
    fixtures = ['airmozilla/manage/tests/main_testdata.json']
# test that a starred event can be synced
# test that an unstarred event can be synced
# test that unchanged events remain that way
# test that unknown event id does the right thing (whatever that is)
# test that the proper list is returned from a get
# test that the proper list of starred events is displayed
# add star, sync 
# remove star, add different star, sync

# test what happens when a user isn't logged in


    def setUp(self):
        super(TestStarredEvent, self).setUp()

        # create the url
        self.url = reverse('starred:sync_starred_events')
        # so, let's sign in
        self.user =  self._login(username='lisa')

    def create_event(self, title):
        # instantiate test event
        event = Event.objects.get(title='Test event')
        event_count = Event.objects.count();

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
        eq_(structure, {"ids": []})

        # add an event id to the list
        structure['ids'].append(event1.id)
        # send synced list to browser
        response = self.client.post(url, {'ids': structure['ids']})
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {"ids": [event1.id]})


    def test_removed_starred_event(self):
        url = self.url
        event1 = Event.objects.get(title='Test event')
        event2 = self.create_event('Test event 2')

        StarredEvents.objects.create(user=self.user, event=event1)
        StarredEvents.objects.create(user=self.user, event=event2)

        response = self.client.post(url, {'ids': [event1.id]})
        eq_(response.status_code, 200)

        ok_(StarredEvents.objects.filter(event=event1.id))
        ok_(not StarredEvents.objects.filter(event=event2.id))

        event2.delete()

    def test_invalid_starred_event_id(self):

        url = self.url
        event1 = Event.objects.get(title='Test event')

        # pass url to the browser
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # get the empty list of event ids in json format 
        structure = json.loads(response.content)
        eq_(structure, {"ids": []})

        # add event id to the list
        structure['ids'].append(event1.id)
        # send list to the browser
        response = self.client.post(url, {'ids': structure['ids']})
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {"ids": [event1.id]})

        # delete event
        new_event = event1.delete()
        # send updated list to the browser
        response = self.client.post(url, {'ids': structure['ids']})
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {"ids": []})


    def test_anonymous_user(self):
        # log out user from setUp()
        self.client.logout()

        url = self.url

        send = {'ids': [23, 24]}

        # send list to the browser
        response = self.client.post(url, send)
        receive = json.loads(response.content)
        # verify the list is returned to the user
        eq_(send, receive)
