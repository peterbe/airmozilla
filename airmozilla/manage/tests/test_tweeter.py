import os
import datetime
from nose.tools import eq_, ok_
import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.conf import settings

from funfactory.urlresolvers import reverse

from airmozilla.manage.tweeter import send_tweet
from airmozilla.main.models import (
    Event,
    EventTweet
)


class TweeterTestCase(TestCase):
    fixtures = ['airmozilla/manage/tests/main_testdata.json']

    event_base_data = {
        'status': Event.STATUS_SCHEDULED,
        'description': '...',
        'participants': 'Tim Mickel',
        'privacy': 'public',
        'location': '1',
        'category': '7',
        'channels': '1',
        'tags': 'xxx',
        'template': '1',
        'start_time': '2012-3-4 12:00',
        'timezone': 'US/Pacific'
    }
    placeholder = 'airmozilla/manage/tests/firefox.png'

    def setUp(self):
        super(TweeterTestCase, self).setUp()
        settings.TWITTER_USERNAME = 'mrtester'
        settings.TWITTER_CONSUMER_SECRET = 'anything'
        settings.TWITTER_CONSUMER_KEY = 'anything'
        settings.TWITTER_ACCESS_TOKEN = 'anything'
        settings.TWITTER_ACCESS_TOKEN_SECRET = 'anything'

        self.user = User.objects.create_superuser('fake', 'fake@f.com', 'fake')
        assert self.client.login(username='fake', password='fake')

    @mock.patch('twython.Twython')
    def test_send_tweet_without_image(self, mocked_twython):
        event = Event.objects.get(title='Test event')
        event_tweet = EventTweet.objects.create(
            event=event,
            text=u'\xa310,000 for a cup of tea? #testing',
        )
        assert not event_tweet.sent_date
        assert not event_tweet.tweet_id

        def mocked_updateStatus(status):
            eq_(status, event_tweet.text.encode('utf-8'))
            return {'id': '0000000001'}

        mocker = mock.MagicMock()
        mocker.updateStatus.side_effect = mocked_updateStatus
        mocked_twython.return_value = mocker

        send_tweet(event_tweet)
        # fetch it again, to assure it got saved
        event_tweet = EventTweet.objects.get(pk=event_tweet.pk)
        ok_(not event_tweet.error)
        ok_(event_tweet.sent_date)
        eq_(event_tweet.tweet_id, '0000000001')

    @mock.patch('twython.Twython')
    def test_send_tweet_with_image(self, mocked_twython):
        event = Event.objects.get(title='Test event')
        with open(self.placeholder) as fp:
            response = self.client.post(
                reverse('manage:event_edit', args=(event.pk,)),
                dict(self.event_base_data,
                     title=event.title,
                     placeholder_img=fp)
            )
            assert response.status_code == 302, response.status_code
        event = Event.objects.get(pk=event.pk)
        assert event.placeholder_img
        event_tweet = EventTweet.objects.create(
            event=event,
            text=u'\xa310,000 for a cup of tea? #testing',
            include_placeholder=True
        )
        assert not event_tweet.sent_date
        assert not event_tweet.tweet_id

        def mocked_updateStatusWithMedia(file_path, status):
            ok_(os.path.isfile(file_path))
            eq_(status, event_tweet.text.encode('utf-8'))
            return {'id': '0000000001'}

        mocker = mock.MagicMock()
        mocker.updateStatusWithMedia.side_effect = mocked_updateStatusWithMedia
        mocked_twython.return_value = mocker

        send_tweet(event_tweet)
        # fetch it again, to assure it got saved
        event_tweet = EventTweet.objects.get(pk=event_tweet.pk)
        ok_(not event_tweet.error)
        ok_(event_tweet.sent_date)
        eq_(event_tweet.tweet_id, '0000000001')

    @mock.patch('twython.Twython')
    def test_send_tweet_with_error(self, mocked_twython):
        event = Event.objects.get(title='Test event')
        event_tweet = EventTweet.objects.create(
            event=event,
            text=u'\xa310,000 for a cup of tea? #testing',
        )
        assert not event_tweet.sent_date
        assert not event_tweet.tweet_id

        def mocked_updateStatus(status):
            raise NameError('bla')

        mocker = mock.MagicMock()
        mocker.updateStatus.side_effect = mocked_updateStatus
        mocked_twython.return_value = mocker

        send_tweet(event_tweet)
        # fetch it again, to assure it got saved
        event_tweet = EventTweet.objects.get(pk=event_tweet.pk)
        ok_(event_tweet.error)
        ok_(event_tweet.sent_date)
        ok_(not event_tweet.tweet_id)
