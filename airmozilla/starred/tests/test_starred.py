import json

from django.test import TestCase
from django.contrib.auth.models import User

from funfactory.urlresolvers import reverse
from nose.tools import eq_, ok_

from airmozilla.main.models import Event
from airmozilla.starred.models import (
    StarredEvents,
)


class TestStarredEvent(TestCase):
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
        User.objects.create_user('lisa', password='secret')
        assert self.client.login(username='lisa', password='secret')

        # instantiate test event
        event = Event.objects.get(title='Test event')
        # create more events 
        Event.objects.create(
            title='A Good Event',
            slug='event1',
            description=event.description,
            start_time=event.start_time,
            privacy=Event.PRIVACY_PUBLIC,
            placeholder_img=event.placeholder_img,
            location=event.location,
        )
        Event.objects.create(
            title='A Great Event',
            slug='event2',
            description=event.description,
            start_time=event.start_time,
            privacy=Event.PRIVACY_PUBLIC,
            placeholder_img=event.placeholder_img,
            location=event.location,
        )
        Event.objects.create(
            title='The Best Event',
            slug='event3',
            description=event.description,
            start_time=event.start_time,
            privacy=Event.PRIVACY_PUBLIC,
            placeholder_img=event.placeholder_img,
            location=event.location,
        )
        # get events from the database
        self.events = Event.objects.all()

    def test_sync_starred_events(self):

        url = self.url
        events = self.events

        # pass url to the browser
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # get the empty list of event ids in json format 
        structure = json.loads(response.content)
        eq_(structure, {"ids": []})

        # add an event id to the list
        structure['ids'].append(events[0].id)
        # send synced list to browser
        response = self.client.post(
            url,
            content_type='application/json',
            data=json.dumps(structure)
        )
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {"ids": [events[0].id]})

    def test_remove_starred_event(self):

        url = self.url
        events = self.events

        # pass url to the browser
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # get the empty list of event ids in json format 
        structure = json.loads(response.content)
        eq_(structure, {"ids": []})

        # add event id to the list
        structure['ids'].append(events[1].id)
        # send list to the browser
        response = self.client.post(
            url,
            content_type='application/json',
            data=json.dumps(structure)
        )
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {"ids": [events[1].id]})

        # add another event id to the list
        structure['ids'].append(events[2].id)
        # send list to the browser
        response = self.client.post(
            url,
            content_type='application/json',
            data=json.dumps(structure)
        )
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {"ids": [events[1].id, events[2].id]})

        # remove an event id from the list
        structure['ids'].remove(events[1].id)
        # send list to the browser
        response = self.client.post(
            url,
            content_type='application/json',
            data=json.dumps(structure)
        )
        # get the list and verify event id was removed
        structure = json.loads(response.content)
        eq_(structure, {"ids": [events[2].id]})


    def test_invalid_starred_event_id(self):

        url = self.url
        events = self.events

        # pass url to the browser
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # get the empty list of event ids in json format 
        structure = json.loads(response.content)
        eq_(structure, {"ids": []})

        event = Event.objects.get(title='Test event')
        new_event = Event.objects.create(
            title='The New Event',
            slug='event4',
            description=event.description,
            start_time=event.start_time,
            privacy=Event.PRIVACY_PUBLIC,
            placeholder_img=event.placeholder_img,
            location=event.location,
        )
        # add event id to the list
        structure['ids'].append(new_event.id)
        # send list to the browser
        response = self.client.post(
            url,
            content_type='application/json',
            data=json.dumps(structure)
        )
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {"ids": [new_event.id]})

        # delete event
        new_event = new_event.delete()
        # send updated list to the browser
        response = self.client.post(
            url,
            content_type='application/json',
            data=json.dumps(structure)
        )
        # get the list and verify it was updated
        structure = json.loads(response.content)
        eq_(structure, {"ids": []})


    def test_anonymous_user(self):
        # log out user from setUp()
        self.client.logout()


