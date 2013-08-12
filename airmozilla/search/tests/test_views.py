import datetime

from django.test import TestCase
from django.utils.timezone import utc

from funfactory.urlresolvers import reverse
from nose.tools import eq_, ok_

from airmozilla.main.models import Event


class TestSearch(TestCase):
    fixtures = ['airmozilla/manage/tests/main_testdata.json']
    placeholder = 'airmozilla/manage/tests/firefox.png'

    def setUp(self):
        super(TestSearch, self).setUp()
        from django.db import connection
        cursor = connection.cursor()
        from _mysql_exceptions import Warning as MySQLWarning
        try:
            cursor.execute("ALTER TABLE main_event ADD FULLTEXT KEY (title)")
            cursor.execute("ALTER TABLE main_event ADD FULLTEXT KEY (description, short_description)")
        except MySQLWarning:
            print "Warning"

    def test_basic_search(self):
        Event.objects.all().delete()
        assert not Event.objects.all().count()
        today = datetime.datetime.utcnow()
        event = Event.objects.create(
            title='Entirely Different',
            slug=today.strftime('test-event-%Y%m%d'),
            start_time=today.replace(tzinfo=utc),
            placeholder_img=self.placeholder,
            status=Event.STATUS_INITIATED,
            description="These are my words."
        )
        from time import sleep
        #sleep(3)
        assert event not in Event.objects.approved()

        url = reverse('search:home')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        response = self.client.get(url, {'q': 'entirely'})
        eq_(response.status_code, 200)
        ok_('Nothing found' in response.content)

        event.status = Event.STATUS_SCHEDULED
        event.save()
        assert event in Event.objects.approved()
        assert event.privacy == Event.PRIVACY_PUBLIC

        response = self.client.get(url, {'q': 'words'})
        eq_(response.status_code, 200)
        ok_('Nothing found' not in response.content)
        ok_(event.title in response.content)
