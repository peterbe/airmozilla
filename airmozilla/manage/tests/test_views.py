import os
import re
import cgi
import datetime
import json
import random
from cStringIO import StringIO

from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.contrib.flatpages.models import FlatPage
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from django.core import mail
from django.utils.timezone import utc

from funfactory.urlresolvers import reverse

from nose.tools import eq_, ok_
import mock

from airmozilla.main.models import (
    Approval,
    Category,
    Event,
    EventTweet,
    EventOldSlug,
    Location,
    Participant,
    Template,
    Channel,
    Tag,
    SuggestedEvent,
    SuggestedEventComment,
    VidlySubmission,
    URLMatch,
    URLTransform,
    EventHitStats
)

from .test_vidly import (
    SAMPLE_XML,
    SAMPLE_MEDIALIST_XML,
    SAMPLE_INVALID_LINKS_XML
)


class ManageTestCase(TestCase):
    fixtures = ['airmozilla/manage/tests/main_testdata.json']

    def setUp(self):
        self.user = User.objects.create_superuser('fake', 'fake@f.com', 'fake')
        assert self.client.login(username='fake', password='fake')

    def _delete_test(self, obj, remove_view, redirect_view):
        """Common test for deleting an object in the management interface,
           checking that it was deleted properly, and ensuring that an improper
           delete request does not remove the object."""
        model = obj.__class__
        url = reverse(remove_view, kwargs={'id': obj.id})
        self.client.get(url)
        obj = model.objects.get(id=obj.id)
        ok_(obj)  # the template wasn't deleted because we didn't use POST
        response_ok = self.client.post(url)
        self.assertRedirects(response_ok, reverse(redirect_view))
        obj = model.objects.filter(id=obj.id).exists()
        ok_(not obj)


class TestPermissions(ManageTestCase):
    def test_unauthorized(self):
        """ Client with no log in - should be rejected. """
        self.client.logout()
        response = self.client.get(reverse('manage:home'))
        self.assertRedirects(response, settings.LOGIN_URL
                             + '?next=' + reverse('manage:home'))

    def test_not_staff(self):
        """ User is not staff - should be rejected. """
        self.user.is_staff = False
        self.user.save()
        response = self.client.get(reverse('manage:home'))
        self.assertRedirects(response, settings.LOGIN_URL
                             + '?next=' + reverse('manage:home'))

    def test_staff_home(self):
        """ User is staff - should get an OK homepage. """
        response = self.client.get(reverse('manage:home'))
        eq_(response.status_code, 200)

    def test_staff_logout(self):
        """ Log out makes admin inaccessible. """
        self.client.get(reverse('auth:logout'))
        response = self.client.get(reverse('manage:home'))
        self.assertRedirects(response, settings.LOGIN_URL
                             + '?next=' + reverse('manage:home'))


class TestDashboard(ManageTestCase):

    # XXX Using `override_settings` doesn't work because of a bug in `tower`.
    # Once that's fixed start using `override_settings` in the tests instead.
    #@override_settings(ADMINS=(('Bob', 'bob@example.com'),))
    def test_dashboard(self):
        self.user.is_superuser = False
        self.user.save()
        _admins_before = settings.ADMINS
        settings.ADMINS = (('Bob', 'bob@example.com'),)
        try:
            response = self.client.get(reverse('manage:home'))
            eq_(response.status_code, 200)
            ok_('bob@example.com' in response.content)
            # create a superuser
            self.user.is_superuser = True
            assert self.user.email
            self.user.save()
            response = self.client.get(reverse('manage:home'))
            eq_(response.status_code, 200)
            ok_('bob@example.com' not in response.content)
            ok_(self.user.email in response.content)
        finally:
            settings.ADMINS = _admins_before

    def test_cache_busting_headers(self):
        # viewing any of the public pages should NOT have it
        response = self.client.get('/')
        eq_(response.status_code, 200)
        ok_('no-store' not in response.get('Cache-Control', ''))

        response = self.client.get(reverse('manage:home'))
        eq_(response.status_code, 200)
        ok_('no-store' in response['Cache-Control'])


class TestUsersAndGroups(ManageTestCase):
    def test_user_group_pages(self):
        """User and group listing pages respond with success."""
        response = self.client.get(reverse('manage:users'))
        eq_(response.status_code, 200)
        response = self.client.get(reverse('manage:users'), {'page': 5000})
        eq_(response.status_code, 200)
        response = self.client.get(reverse('manage:groups'))
        eq_(response.status_code, 200)

    def test_user_edit(self):
        """Add superuser and staff status via the user edit form."""
        user = User.objects.create_user('no', 'no@no.com', 'no')
        response = self.client.post(
            reverse('manage:user_edit', kwargs={'id': user.id}),
            {
                'is_superuser': 'on',
                'is_staff': 'on',
                'is_active': 'on'
            }
        )
        self.assertRedirects(response, reverse('manage:users'))
        user = User.objects.get(id=user.id)
        ok_(user.is_superuser)
        ok_(user.is_staff)

    def test_group_add(self):
        """Add a group and verify its creation."""
        response = self.client.get(reverse('manage:group_new'))
        eq_(response.status_code, 200)
        response = self.client.post(
            reverse('manage:group_new'),
            {
                'name': 'fake_group'
            }
        )
        self.assertRedirects(response, reverse('manage:groups'))
        group = Group.objects.get(name='fake_group')
        ok_(group is not None)
        eq_(group.name, 'fake_group')

    def test_group_edit(self):
        """Group editing: group name change form sucessfully changes name."""
        group, __ = Group.objects.get_or_create(name='testergroup')
        response = self.client.get(reverse('manage:group_edit',
                                           kwargs={'id': group.id}))
        eq_(response.status_code, 200)
        response = self.client.post(
            reverse('manage:group_edit', kwargs={'id': group.id}),
            {
                'name': 'newtestergroup  '
            }
        )
        self.assertRedirects(response, reverse('manage:groups'))
        group = Group.objects.get(id=group.id)
        eq_(group.name, 'newtestergroup')

    def test_group_remove(self):
        group, __ = Group.objects.get_or_create(name='testergroup')
        self._delete_test(group, 'manage:group_remove', 'manage:groups')

    def test_user_search(self):
        """Searching for a created user redirects properly; otherwise fail."""
        user = User.objects.create_user('t', 'testuser@mozilla.com')
        response_ok = self.client.post(
            reverse('manage:users'),
            {
                'email': user.email
            }
        )
        self.assertRedirects(
            response_ok,
            reverse('manage:user_edit', kwargs={'id': user.id})
        )
        response_fail = self.client.post(
            reverse('manage:users'),
            {
                'email': 'bademail@mozilla.com'
            }
        )
        eq_(response_fail.status_code, 200)


class TestEvents(ManageTestCase):
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

    def test_event_request(self):
        """Event request responses and successful creation in the db."""
        response = self.client.get(reverse('manage:event_request'))
        eq_(response.status_code, 200)
        with open(self.placeholder) as fp:
            response_ok = self.client.post(
                reverse('manage:event_request'),
                dict(self.event_base_data, placeholder_img=fp,
                     title='Airmozilla Launch Test')
            )
            response_fail = self.client.post(
                reverse('manage:event_request'),
                {
                    'title': 'Test fails, not enough data!',
                }
            )
            response_cancel = self.client.post(
                reverse('manage:event_request'),
                {
                    'cancel': 'yes'
                }
            )

        self.assertRedirects(response_ok, reverse('manage:events'))
        eq_(response_fail.status_code, 200)
        event = Event.objects.get(title='Airmozilla Launch Test')
        eq_(event.location, Location.objects.get(id=1))
        eq_(event.creator, self.user)
        eq_(response_cancel.status_code, 302)
        self.assertRedirects(response_cancel, reverse('manage:events'))

    def test_event_request_sorted_dropdowns(self):
        # first create a bunch of categories
        names = ['Category%s' % x for x in range(5)]
        random.shuffle(names)
        [Category.objects.create(name=x) for x in names]

        response = self.client.get(reverse('manage:event_request'))
        # the order matters
        c = response.content
        ok_(-1 <
            c.find('>Category2<') <
            c.find('>Category3<') <
            c.find('>Category4<'))

    def test_event_request_with_approvals(self):
        group1, = Group.objects.all()
        group2 = Group.objects.create(name='Group2')
        permission = Permission.objects.get(codename='change_approval')
        group1.permissions.add(permission)
        group2.permissions.add(permission)
        group_user = User.objects.create_user(
            'username',
            'em@ail.com',
            'secret'
        )
        group_user.groups.add(group2)

        inactive_user = User.objects.create_user(
            'longgone',
            'long@gone.com',
            'secret'
        )
        inactive_user.is_active = False
        inactive_user.save()
        inactive_user.groups.add(group2)

        long_description_with_html = (
            'The researchers took a "theoretical" approach instead, using '
            'something known as the no-signalling conditions. They '
            'considered an entangled system with a set of independent '
            'physical attributes, some observable, some hidden variables. '
            '\n\n'
            'Next, they allowed the state of the hidden variables '
            'to propagate faster than the speed of light, which let '
            'them influence the measurements on the separated pieces of '
            'the experiment. '
            '\n\n'
            '<ul>'
            '<li>One</li>'
            '<li>Two</li>'
            '</ul>'
            '\n\n'
            'Baskin & Robbins'
        )

        with open(self.placeholder) as fp:
            response = self.client.post(
                reverse('manage:event_request'),
                dict(self.event_base_data,
                     description=long_description_with_html,
                     placeholder_img=fp,
                     title='Airmozilla Launch Test',
                     approvals=[group1.pk, group2.pk])
            )
            eq_(response.status_code, 302)
        event = Event.objects.get(title='Airmozilla Launch Test')
        approvals = event.approval_set.all()
        eq_(approvals.count(), 2)
        # this should send an email to all people in those groups
        email_sent = mail.outbox[-1]
        ok_(group_user.email in email_sent.to)
        ok_(inactive_user.email not in email_sent.to)
        ok_(event.title in email_sent.subject)
        ok_(reverse('manage:approvals') in email_sent.body)
        ok_('Baskin & Robbins' in email_sent.body)  # & not &amp;
        ok_('<li>One</li>' not in email_sent.body)
        ok_('* One\n' in email_sent.body)
        # edit it and drop the second group
        response_ok = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.id}),
            dict(self.event_base_data, title='Different title',
                 approvals=[group1.pk])
        )
        eq_(response_ok.status_code, 302)
        event = Event.objects.get(title='Different title')
        approvals = event.approval_set.all()
        eq_(approvals.count(), 1)

    def test_tag_autocomplete(self):
        """Autocomplete makes JSON for fixture tags and a nonexistent tag."""
        response = self.client.get(
            reverse('manage:tag_autocomplete'),
            {
                'q': 'tes'
            }
        )
        eq_(response.status_code, 200)
        parsed = json.loads(response.content)
        ok_('tags' in parsed)
        tags = [t['text'] for t in parsed['tags'] if 'text' in t]
        eq_(len(tags), 3)
        ok_(('tes' in tags) and ('test' in tags) and ('testing' in tags))

    def test_participant_autocomplete(self):
        """Autocomplete makes JSON pages and correct results for fixtures."""
        response = self.client.get(
            reverse('manage:participant_autocomplete'),
            {
                'q': 'Ti'
            }
        )
        eq_(response.status_code, 200)
        parsed = json.loads(response.content)
        ok_('participants' in parsed)
        participants = [p['text'] for p in parsed['participants']
                        if 'text' in p]
        eq_(len(participants), 1)
        ok_('Tim Mickel' in participants)
        response_fail = self.client.get(
            reverse('manage:participant_autocomplete'),
            {
                'q': 'ickel'
            }
        )
        eq_(response_fail.status_code, 200)
        parsed_fail = json.loads(response_fail.content)
        eq_(parsed_fail, {'participants': []})
        response_blank = self.client.get(
            reverse('manage:participant_autocomplete'),
            {
                'q': ''
            }
        )
        eq_(response_blank.status_code, 200)
        parsed_blank = json.loads(response_blank.content)
        eq_(parsed_blank, {'participants': []})

    def test_events(self):
        """The events page responds successfully."""
        response = self.client.get(reverse('manage:events'))
        eq_(response.status_code, 200)

    def test_find_event(self):
        """Find event responds with filtered results or raises error."""
        response_ok = self.client.get(reverse('manage:events'),
                                      {'title': 'event'})
        eq_(response_ok.status_code, 200)
        ok_(response_ok.content.find('Test event') >= 0)
        response_fail = self.client.get(reverse('manage:events'),
                                        {'title': 'laskdjflkajdsf'})
        eq_(response_fail.status_code, 200)
        ok_(response_fail.content.find('No event') >= 0)

    def test_event_edit_slug(self):
        """Test editing an event - modifying an event's slug
           results in a correct EventOldSlug."""
        event = Event.objects.get(title='Test event')
        response = self.client.get(reverse('manage:event_edit',
                                           kwargs={'id': event.id}))

        eq_(response.status_code, 200)
        response_ok = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.id}),
            dict(self.event_base_data, title='Tested event')
        )
        self.assertRedirects(response_ok, reverse('manage:events'))
        ok_(EventOldSlug.objects.get(slug='test-event', event=event))
        event = Event.objects.get(title='Tested event')
        eq_(event.slug, 'tested-event')
        eq_(event.modified_user, self.user)
        response_fail = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.id}),
            {
                'title': 'not nearly enough data',
                'status': Event.STATUS_SCHEDULED
            }
        )
        eq_(response_fail.status_code, 200)

    def test_event_edit_templates(self):
        """Event editing results in correct template environments."""
        event = Event.objects.get(title='Test event')
        url = reverse('manage:event_edit', kwargs={'id': event.id})
        response_ok = self.client.post(
            url,
            dict(self.event_base_data, title='template edit',
                 template_environment='tv1=\'hi\'\ntv2===')
        )
        self.assertRedirects(response_ok, reverse('manage:events'))
        event = Event.objects.get(id=event.id)
        eq_(event.template_environment, {'tv1': "'hi'", 'tv2': '=='})
        response_edit_page = self.client.get(url)
        eq_(response_edit_page.status_code, 200,
            'Edit page renders OK with a specified template environment.')
        response_fail = self.client.post(
            url,
            dict(self.event_base_data, title='template edit',
                 template_environment='failenvironment')
        )
        eq_(response_fail.status_code, 200)

    def test_timezones(self):
        """Event requests/edits demonstrate correct timezone math."""

        def _tz_test(url, tzdata, correct_date, msg):
            with open(self.placeholder) as fp:
                base_data = dict(self.event_base_data,
                                 title='timezone test', placeholder_img=fp)
                self.client.post(url, dict(base_data, **tzdata))
            event = Event.objects.get(title='timezone test',
                                      start_time=correct_date)
            ok_(event, msg + ' vs. ' + str(event.start_time))
        url = reverse('manage:event_request')
        _tz_test(
            url,
            {
                'start_time': '2012-08-03 12:00',
                'timezone': 'US/Eastern'
            },
            datetime.datetime(2012, 8, 3, 16).replace(tzinfo=utc),
            'Event request summer date - Eastern UTC-04 input'
        )
        _tz_test(
            url,
            {
                'start_time': '2012-11-30 3:00',
                'timezone': 'Europe/Paris'
            },
            datetime.datetime(2012, 11, 30, 2).replace(tzinfo=utc),
            'Event request winter date - CET UTC+01 input'
        )
        event = Event.objects.get(title='Test event')
        url = reverse('manage:event_edit', kwargs={'id': event.id})
        _tz_test(
            url,
            {
                'start_time': '2012-08-03 15:00',
                'timezone': 'US/Pacific'
            },
            datetime.datetime(2012, 8, 3, 22).replace(tzinfo=utc),
            'Modify event summer date - Pacific UTC-07 input'
        )
        _tz_test(
            url,
            {
                'start_time': '2012-12-25 15:00',
                'timezone': 'US/Pacific'
            },
            datetime.datetime(2012, 12, 25, 23).replace(tzinfo=utc),
            'Modify event winter date - Pacific UTC-08 input'
        )

    def test_event_archive(self):
        """Event archive page loads and shows correct archive_time behavior."""
        event = Event.objects.get(title='Test event')
        event.archive_time = None
        # also, make it non-public
        event.privacy = Event.PRIVACY_COMPANY
        event.save()
        url = reverse('manage:event_archive', kwargs={'id': event.id})
        response_ok = self.client.get(url)
        eq_(response_ok.status_code, 200)
        # the `token_protection` should be forced on
        ok_('Required for non-public events' in response_ok.content)

        response_ok = self.client.post(url)
        self.assertRedirects(response_ok, reverse('manage:events'))
        event_modified = Event.objects.get(id=event.id)
        eq_(event_modified.status, Event.STATUS_SCHEDULED)
        now = (
            datetime.datetime.utcnow()
            .replace(tzinfo=utc, microsecond=0)
        )
        # because this `now` can potentially be different in the tests
        # compared (if the tests run slow) to the views,
        # it's safer to not look at the seconds
        eq_(
            event_modified.archive_time.strftime('%d %H:%M'),
            now.strftime('%d %H:%M')
        )

    def test_event_archive_with_vidly_template(self):
        """Event archive page loads and shows correct archive_time behavior."""
        vidly_template = Template.objects.create(name='Vid.ly HD')

        event = Event.objects.get(title='Test event')
        event.archive_time = None
        event.save()

        url = reverse('manage:event_archive', kwargs={'id': event.id})
        response_ok = self.client.post(url, {
            'template': vidly_template.pk,
            'template_environment': 'tag=abc123',
        })
        self.assertRedirects(response_ok, reverse('manage:events'))
        event_modified = Event.objects.get(id=event.id)
        eq_(event_modified.archive_time, None)
        eq_(event_modified.status, Event.STATUS_PENDING)

    def test_event_duplication(self):
        event = Event.objects.get(title='Test event')
        url = reverse('manage:event_duplicate', args=(event.id,))
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('value="Test event"' in response.content)

    def test_event_duplication_custom_channels(self):
        ch = Channel.objects.create(
            name='Custom Culture',
            slug='custom-culture'
        )
        event = Event.objects.get(title='Test event')
        event.channels.filter(slug=settings.DEFAULT_CHANNEL_SLUG).delete()
        event.channels.add(ch)
        event.save()

        url = reverse('manage:event_duplicate', args=(event.id,))
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('value="Test event"' in response.content)
        # expect a <option> tag selected with this name
        tags = re.findall(
            '<option (.*?)>([\w\s]+)</option>',
            response.content,
            flags=re.M
        )
        for attrs, value in tags:
            if value == ch.name:
                ok_('selected' in attrs)

    def test_event_preview_shortcut(self):
        # become anonymous (reverse what setUp() does)
        self.client.logout()

        # view it anonymously
        event = Event.objects.get(title='Test event')
        url = reverse('main:event', args=(event.slug,))
        response = self.client.get(url)
        eq_(response.status_code, 200)
        edit_url = reverse('manage:event_edit', args=(event.pk,))
        ok_(edit_url not in response.content)
        # now log in
        assert self.client.login(username='fake', password='fake')
        # check that you can view the edit page
        response = self.client.get(edit_url)
        eq_(response.status_code, 200)
        # and now the real test
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_(edit_url in response.content)

    @mock.patch('airmozilla.manage.vidly.urllib2')
    def test_vidly_url_to_shortcode(self, p_urllib2):
        event = Event.objects.get(title='Test event')
        assert event.privacy == Event.PRIVACY_PUBLIC
        url = reverse('manage:vidly_url_to_shortcode', args=(event.pk,))

        def mocked_urlopen(request):
            return StringIO("""
            <?xml version="1.0"?>
            <Response>
              <Message>All medias have been added.</Message>
              <MessageCode>2.1</MessageCode>
              <BatchID>47520</BatchID>
              <Success>
                <MediaShortLink>
                  <SourceFile>http://www.com/file.flv</SourceFile>
                  <ShortLink>8oxv6x</ShortLink>
                  <MediaID>13969839</MediaID>
                  <QRCode>http://vid.ly/8oxv6x/qrcodeimg</QRCode>
                  <HtmlEmbed>code code</HtmlEmbed>
                  <EmailEmbed>more code code</EmailEmbed>
                </MediaShortLink>
              </Success>
            </Response>
            """)
        p_urllib2.urlopen = mocked_urlopen

        response = self.client.get(url)
        eq_(response.status_code, 405)

        response = self.client.post(url, {
            'url': 'not a url'
        })
        eq_(response.status_code, 400)

        match = URLMatch.objects.create(
            name='Always Be Safe',
            string='^http://'
        )
        URLTransform.objects.create(
            match=match,
            find='^http://',
            replace_with='https://'
        )
        response = self.client.post(url, {
            'url': 'http://www.com/'
        })
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content['shortcode'], '8oxv6x')
        eq_(content['url'], 'https://www.com/')

        arguments = list(p_urllib2.Request.mock_calls[0])[1]
        # the first argument is the URL
        ok_('vid.ly' in arguments[0])
        # the second argument is querystring containing the XML used
        data = cgi.parse_qs(arguments[1])
        xml = data['xml'][0]
        ok_('<HD>YES</HD>' not in xml)
        ok_('<HD>NO</HD>' in xml)
        ok_('<SourceFile>https://www.com/</SourceFile>' in xml)

        # re-fetch it
        match = URLMatch.objects.get(pk=match.pk)
        eq_(match.use_count, 1)

    @mock.patch('airmozilla.manage.vidly.urllib2')
    def test_vidly_url_to_shortcode_with_forced_protection(self, p_urllib2):
        event = Event.objects.get(title='Test event')
        event.privacy = Event.PRIVACY_COMPANY
        event.save()
        url = reverse('manage:vidly_url_to_shortcode', args=(event.pk,))

        def mocked_urlopen(request):
            return StringIO("""
            <?xml version="1.0"?>
            <Response>
              <Message>All medias have been added.</Message>
              <MessageCode>2.1</MessageCode>
              <BatchID>47520</BatchID>
              <Success>
                <MediaShortLink>
                  <SourceFile>http://www.com/file.flv</SourceFile>
                  <ShortLink>8oxv6x</ShortLink>
                  <MediaID>13969839</MediaID>
                  <QRCode>http://vid.ly/8oxv6x/qrcodeimg</QRCode>
                  <HtmlEmbed>code code</HtmlEmbed>
                  <EmailEmbed>more code code</EmailEmbed>
                </MediaShortLink>
              </Success>
            </Response>
            """)
        p_urllib2.urlopen = mocked_urlopen

        response = self.client.post(url, {
            'url': 'http://www.com/'
        })
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content['shortcode'], '8oxv6x')

        submission, = VidlySubmission.objects.all()
        ok_(submission.token_protection)
        ok_(not submission.hd)

    @mock.patch('airmozilla.manage.vidly.urllib2')
    def test_vidly_url_to_shortcode_with_hd(self, p_urllib2):
        event = Event.objects.get(title='Test event')
        url = reverse('manage:vidly_url_to_shortcode', args=(event.pk,))

        def mocked_urlopen(request):
            return StringIO("""
            <?xml version="1.0"?>
            <Response>
              <Message>All medias have been added.</Message>
              <MessageCode>2.1</MessageCode>
              <BatchID>47520</BatchID>
              <Success>
                <MediaShortLink>
                  <SourceFile>http://www.com/file.flv</SourceFile>
                  <ShortLink>8oxv6x</ShortLink>
                  <MediaID>13969839</MediaID>
                  <QRCode>http://vid.ly/8oxv6x/qrcodeimg</QRCode>
                  <HtmlEmbed>code code</HtmlEmbed>
                  <EmailEmbed>more code code</EmailEmbed>
                </MediaShortLink>
              </Success>
            </Response>
            """)
        p_urllib2.urlopen = mocked_urlopen

        response = self.client.post(url, {
            'url': 'http://www.com/',
            'hd': True,
        })
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content['shortcode'], '8oxv6x')

        arguments = list(p_urllib2.Request.mock_calls[0])[1]
        # the first argument is the URL
        ok_('vid.ly' in arguments[0])
        # the second argument is querystring containing the XML used
        data = cgi.parse_qs(arguments[1])
        xml = data['xml'][0]
        ok_('<HD>YES</HD>' in xml)
        ok_('<HD>NO</HD>' not in xml)

    def test_events_autocomplete(self):
        event = Event.objects.get(title='Test event')
        event2 = Event.objects.create(
            title='The Other Cool Title Event',
            description=event.description,
            start_time=event.start_time,
        )
        eq_(Event.objects.all().count(), 2)
        url = reverse('manage:event_autocomplete')

        response = self.client.get(url)
        eq_(response.status_code, 400)

        response = self.client.get(url, {'q': 'something', 'max': 'nan'})
        eq_(response.status_code, 400)

        response = self.client.get(url, {'q': 'eVEnt'})
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content, ['Test event', 'The Other Cool Title Event'])

        response = self.client.get(url, {'q': 'EVen', 'max': 1})
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content, ['Test event'])

        response = self.client.get(url, {'q': 'E'})
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content, [])

        response = self.client.get(url, {'q': 'COOL'})
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content, ['The Other Cool Title Event'])

        response = self.client.get(url, {'q': 'COO'})
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content, ['The Other Cool Title Event'])

        response = self.client.get(url, {'q': 'THE'})
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content, [])

        # the autocomplete caches the same search
        event2.title = event2.title.replace('Cool', 'Brilliant')
        event2.save()

        response = self.client.get(url, {'q': 'COol'})
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content, ['The Other Cool Title Event'])

        # but if the query is different it should work
        response = self.client.get(url, {'q': 'brill'})
        eq_(response.status_code, 200)
        content = json.loads(response.content)
        eq_(content, ['The Other Brilliant Title Event'])

    def test_overwrite_old_slug(self):
        # you create an event, change the slug and change it back
        with open(self.placeholder) as fp:
            response = self.client.post(
                reverse('manage:event_request'),
                dict(self.event_base_data, placeholder_img=fp,
                     title='Launch')
            )
            eq_(response.status_code, 302)
        event = Event.objects.get(slug='launch')
        url = reverse('main:event', args=('launch',))
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # now edit the slug
        response = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.pk}),
            dict(self.event_base_data,
                 title='Different title',
                 slug='different',)
        )
        eq_(response.status_code, 302)
        assert Event.objects.get(slug='different')

        old_url = url
        url = reverse('main:event', args=('different',))
        response = self.client.get(url)
        eq_(response.status_code, 200)

        response = self.client.get(old_url)
        eq_(response.status_code, 302)
        self.assertRedirects(response, url)

        # but suppose we change our mind back
        response = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.pk}),
            dict(self.event_base_data,
                 title='Launch title',
                 slug='launch',)
        )
        eq_(response.status_code, 302)
        event = Event.objects.get(slug='launch')

        old_url = url
        url = reverse('main:event', args=('launch',))
        response = self.client.get(url)
        eq_(response.status_code, 200)

        response = self.client.get(old_url)
        eq_(response.status_code, 302)
        self.assertRedirects(response, url)

        event.delete()
        response = self.client.get(url)
        eq_(response.status_code, 404)

        response = self.client.get(old_url)
        eq_(response.status_code, 404)

    def test_overwrite_old_slug_twice(self):
        # based on https://bugzilla.mozilla.org/show_bug.cgi?id=850742#c3
        with open(self.placeholder) as fp:
            response = self.client.post(
                reverse('manage:event_request'),
                dict(self.event_base_data, placeholder_img=fp,
                     title='Champagne')
            )
            eq_(response.status_code, 302)
        event = Event.objects.get(slug='champagne')
        # now edit the slug
        response = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.pk}),
            dict(self.event_base_data,
                 title=event.title,
                 slug='somethingelse')
        )

        # back again
        response = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.pk}),
            dict(self.event_base_data,
                 title=event.title,
                 slug='champagne')
        )

        # one last time
        response = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.pk}),
            dict(self.event_base_data,
                 title=event.title,
                 slug='somethingelse')
        )

        url = reverse('main:event', args=('somethingelse',))
        response = self.client.get(url)
        eq_(response.status_code, 200)

        old_url = reverse('main:event', args=('champagne',))
        response = self.client.get(old_url)
        eq_(response.status_code, 302)
        self.assertRedirects(response, url)

    def test_event_request_with_clashing_flatpage(self):
        FlatPage.objects.create(
            url='/egg-plants/',
            title='Egg Plants',
        )
        with open(self.placeholder) as fp:
            response = self.client.post(
                reverse('manage:event_request'),
                dict(self.event_base_data, placeholder_img=fp,
                     title='Egg Plants')
            )
            eq_(response.status_code, 200)
            ok_('Form errors' in response.content)

    def test_event_edit_with_clashing_flatpage(self):
        # if you edit the event and its slug already clashes with a
        # FlatPage, there's little we can do, the FlatPage was added
        # after
        with open(self.placeholder) as fp:
            response = self.client.post(
                reverse('manage:event_request'),
                dict(self.event_base_data, placeholder_img=fp,
                     title='Champagne')
            )
            eq_(response.status_code, 302)

        FlatPage.objects.create(
            url='/egg-plants/',
            title='Egg Plants',
        )

        event = Event.objects.get(slug='champagne')
        # now edit the event without changing the slug
        response = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.pk}),
            dict(self.event_base_data,
                 title="New Title",
                 slug=event.slug)
        )
        # should be ok
        eq_(response.status_code, 302)

        response = self.client.post(
            reverse('manage:event_edit', kwargs={'id': event.pk}),
            dict(self.event_base_data,
                 title="New Title",
                 slug='egg-plants')
        )
        # should NOT be ok
        eq_(response.status_code, 200)
        ok_('Form errors' in response.content)

    def test_event_edit_with_vidly_submissions(self):
        event = Event.objects.get(title='Test event')
        url = reverse('manage:event_edit', args=(event.pk,))

        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('id="vidly-submission"' not in response.content)

        template = event.template
        template.name = 'Vid.ly Fun'
        template.save()

        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('id="vidly-submission"' in response.content)

        VidlySubmission.objects.create(
            event=event,
            url='http://www.file',
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('1 Vid.ly Submission' in response.content)

        # a second one
        VidlySubmission.objects.create(
            event=event,
            url='http://www.file.different.file',
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('2 Vid.ly Submissions' in response.content)

        submissions_url = reverse(
            'manage:event_vidly_submissions',
            args=(event.pk,)
        )
        ok_(submissions_url in response.content)

    @mock.patch('urllib2.urlopen')
    def test_event_edit_with_stuck_pending(self, p_urlopen):

        def mocked_urlopen(request):
            return StringIO(SAMPLE_XML.strip())

        p_urlopen.side_effect = mocked_urlopen

        event = Event.objects.get(title='Test event')
        event.template_environment = {'tag': 'abc123'}
        event.status = Event.STATUS_PENDING
        event.save()

        url = reverse('manage:event_edit', args=(event.pk,))

        template = event.template
        template.name = 'Vid.ly Fun'
        template.save()
        submission = VidlySubmission.objects.create(
            event=event,
            url='http://www.file',
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('1 Vid.ly Submission' in response.content)

        auto_archive_url = reverse(
            'manage:event_archive_auto',
            args=(event.pk,)
        )
        ok_(auto_archive_url not in response.content)
        # the reason it's not there is because the VidlySubmission
        # was made very recently.
        # It will appear if the VidlySubmission does not exist
        submission.submission_time -= datetime.timedelta(hours=1)
        submission.save()
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_(auto_archive_url in response.content)

        # or if there is no VidlySubmission at all
        submission.delete()
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_(auto_archive_url in response.content)

        response = self.client.post(auto_archive_url)
        eq_(response.status_code, 302)
        event = Event.objects.get(pk=event.pk)
        eq_(event.status, Event.STATUS_SCHEDULED)
        ok_(event.archive_time)

    def test_event_vidly_submissions(self):
        event = Event.objects.get(title='Test event')
        template = event.template
        template.name = 'Vid.ly Fun'
        template.save()

        url = reverse('manage:event_vidly_submissions', args=(event.pk,))
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # add one
        VidlySubmission.objects.create(
            event=event,
            url='http://something.long/url.file',
            hd=True,
            token_protection=False,
            tag='abc123',
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('http://something.long/url.file' in response.content)
        ok_('abc123' in response.content)

    def test_event_vidly_submission(self):
        event = Event.objects.get(title='Test event')
        submission = VidlySubmission.objects.create(
            event=event,
            url='http://something.long/url.file',
            hd=True,
            token_protection=False,
            tag='abc123',
            submission_error='Something went wrong',
        )
        url = reverse(
            'manage:event_vidly_submission',
            args=(event.pk, submission.pk)
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data['submission_error'], 'Something went wrong')

        # or as fields
        response = self.client.get(url, {'as_fields': True})
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        ok_(data['fields'])
        first_field = data['fields'][0]
        ok_('key' in first_field)
        ok_('value' in first_field)

    def test_event_hit_stats(self):
        event = Event.objects.get(title='Test event')
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        event.start_time = now - datetime.timedelta(days=400)
        event.archive_time = now - datetime.timedelta(days=365)
        event.save()

        EventHitStats.objects.create(
            event=event,
            total_hits=101,
            shortcode='abc123',
        )

        url = reverse('manage:event_hit_stats')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        # 101 / 365 days ~= 0.3
        ok_('1 year' in response.content)
        ok_('101' in response.content)
        ok_('0.3' in response.content)

    def test_event_edit_without_vidly_template(self):
        """based on https://bugzilla.mozilla.org/show_bug.cgi?id=879725"""
        event = Event.objects.get(title='Test event')
        event.status = Event.STATUS_PENDING
        event.archive_time = None
        event.template = None
        event.save()

        url = reverse('manage:event_edit', args=(event.pk,))
        response = self.client.get(url)
        eq_(response.status_code, 200)

    def test_event_edit_with_suggested_event_comments(self):
        event = Event.objects.get(title='Test event')
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        suggested_event = SuggestedEvent.objects.create(
            user=self.user,
            title=event.title,
            slug=event.slug,
            description=event.description,
            short_description=event.short_description,
            location=event.location,
            start_time=event.start_time,
            accepted=event,
            submitted=now,
        )
        SuggestedEventComment.objects.create(
            suggested_event=suggested_event,
            user=self.user,
            comment='hi!\n"friend"'
        )
        url = reverse('manage:event_edit', args=(event.pk,))
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_(
            'Additional comments from original requested event'
            in response.content
        )
        ok_('hi!<br>&#34;friend&#34;' in response.content)


class TestParticipants(ManageTestCase):
    def test_participant_pages(self):
        """Participants pagination always returns valid pages."""
        response = self.client.get(reverse('manage:participants'))
        eq_(response.status_code, 200)
        response = self.client.get(reverse('manage:participants'),
                                   {'page': 5000})
        eq_(response.status_code, 200)

    def test_participant_find(self):
        """Search filters participants; returns all for bad search."""
        response_ok = self.client.post(
            reverse('manage:participants'),
            {
                'name': 'Tim'
            }
        )
        eq_(response_ok.status_code, 200)
        ok_(response_ok.content.find('Tim') >= 0)
        response_fail = self.client.post(
            reverse('manage:participants'),
            {
                'name': 'Lincoln'
            }
        )
        eq_(response_fail.status_code, 200)
        ok_(response_fail.content.find('Tim') >= 0)

    def test_participant_edit(self):
        """Participant edit page responds OK; bad form results in failure;
        submission induces a change.
        """
        participant = Participant.objects.get(name='Tim Mickel')
        response = self.client.get(reverse('manage:participant_edit',
                                           kwargs={'id': participant.id}))
        eq_(response.status_code, 200)
        response_ok = self.client.post(
            reverse('manage:participant_edit', kwargs={'id': participant.id}),
            {
                'name': 'George Washington',
                'email': 'george@whitehouse.gov',
                'role': Participant.ROLE_PRINCIPAL_PRESENTER,
                'cleared': Participant.CLEARED_YES
            }
        )
        self.assertRedirects(response_ok, reverse('manage:participants'))
        participant_george = Participant.objects.get(id=participant.id)
        eq_(participant_george.name, 'George Washington')
        response_fail = self.client.post(
            reverse('manage:participant_edit', kwargs={'id': participant.id}),
            {
                'name': 'George Washington',
                'email': 'bademail'
            }
        )
        eq_(response_fail.status_code, 200)

    def test_participant_email(self):
        """Participant email page generates a token, redirects properly."""
        participant = Participant.objects.get(name='Tim Mickel')
        participant.clear_token = ''
        participant.save()
        url = reverse('manage:participant_email',
                      kwargs={'id': participant.id})
        response = self.client.get(url)
        eq_(response.status_code, 200)
        participant = Participant.objects.get(name='Tim Mickel')
        ok_(participant.clear_token)
        response_redirect = self.client.post(url)
        self.assertRedirects(response_redirect, reverse('manage:participants'))

    def test_participant_new(self):
        """New participant page responds OK and form works as expected."""
        response = self.client.get(reverse('manage:participant_new'))
        eq_(response.status_code, 200)
        with open('airmozilla/manage/tests/firefox.png') as fp:
            response_ok = self.client.post(
                reverse('manage:participant_new'),
                {
                    'name': 'Mozilla Firefox',
                    'slug': 'mozilla-firefox',
                    'photo': fp,
                    'email': 'mozilla@mozilla.com',
                    'role': Participant.ROLE_PRINCIPAL_PRESENTER,
                    'cleared': Participant.CLEARED_NO
                }
            )
        self.assertRedirects(response_ok, reverse('manage:participants'))
        participant = Participant.objects.get(name='Mozilla Firefox')
        eq_(participant.email, 'mozilla@mozilla.com')
        eq_(participant.creator, self.user)

    def test_participant_remove(self):
        participant = Participant.objects.get(name='Tim Mickel')
        self._delete_test(participant, 'manage:participant_remove',
                          'manage:participants')


class TestCategories(ManageTestCase):
    def test_categories(self):
        """ Categories listing responds OK. """
        response = self.client.get(reverse('manage:categories'))
        eq_(response.status_code, 200)

    def test_category_new(self):
        """ Category form adds new categories. """
        response = self.client.get(reverse('manage:category_new'))
        eq_(response.status_code, 200)

        response_ok = self.client.post(
            reverse('manage:category_new'),
            {
                'name': 'Web Dev Talks '
            }
        )
        self.assertRedirects(response_ok, reverse('manage:categories'))
        ok_(Category.objects.get(name='Web Dev Talks'))
        response_fail = self.client.post(reverse('manage:category_new'))
        eq_(response_fail.status_code, 200)

    def test_category_edit(self):
        """Category edit"""
        category = Category.objects.get(name='testing')
        response = self.client.get(
            reverse('manage:category_edit', args=(category.pk,)),
        )
        eq_(response.status_code, 200)
        ok_('value="testing"' in response.content)
        response = self.client.post(
            reverse('manage:category_edit', args=(category.pk,)),
            {
                'name': 'different',
            }
        )
        eq_(response.status_code, 302)
        category = Category.objects.get(name='different')

    def test_category_delete(self):
        category = Category.objects.get(name='testing')
        self._delete_test(category, 'manage:category_remove',
                          'manage:categories')


class TestChannels(ManageTestCase):
    def test_channels(self):
        """ Channels listing responds OK. """
        response = self.client.get(reverse('manage:channels'))
        eq_(response.status_code, 200)

    def test_channel_new(self):
        """ Channel form adds new channels. """
        # render the form
        response = self.client.get(reverse('manage:channel_new'))
        eq_(response.status_code, 200)

        response_ok = self.client.post(
            reverse('manage:channel_new'),
            {
                'name': ' Web Dev ',
                'slug': 'web-dev',
                'description': '<h1>Stuff</h1>',
                'image_is_banner': True
            }
        )
        self.assertRedirects(response_ok, reverse('manage:channels'))
        ok_(Channel.objects.get(name='Web Dev'))
        ok_(Channel.objects.get(name='Web Dev').image_is_banner)
        response_fail = self.client.post(reverse('manage:channel_new'))
        eq_(response_fail.status_code, 200)

    def test_channel_edit(self):
        """Channel edit"""
        channel = Channel.objects.get(slug='testing')
        response = self.client.get(
            reverse('manage:channel_edit', args=(channel.pk,)),
        )
        eq_(response.status_code, 200)
        ok_('value="testing"' in response.content)
        response = self.client.post(
            reverse('manage:channel_edit', args=(channel.pk,)),
            {
                'name': 'Different',
                'slug': 'different',
                'description': '<p>Other things</p>'
            }
        )
        eq_(response.status_code, 302)
        channel = Channel.objects.get(slug='different')

    def test_channel_delete(self):
        channel = Channel.objects.create(
            name='How Tos',
            slug='how-tos',
        )
        self._delete_test(channel, 'manage:channel_remove',
                          'manage:channels')


class TestTemplates(ManageTestCase):
    def test_templates(self):
        """Templates listing responds OK."""
        response = self.client.get(reverse('manage:templates'))
        eq_(response.status_code, 200)

    def test_template_new(self):
        """New template form responds OK and results in a new template."""
        url = reverse('manage:template_new')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        response_ok = self.client.post(url, {
            'name': 'happy template',
            'content': 'hello!'
        })
        self.assertRedirects(response_ok, reverse('manage:templates'))
        ok_(Template.objects.get(name='happy template'))
        response_fail = self.client.post(url)
        eq_(response_fail.status_code, 200)

    def test_template_edit(self):
        """Template editor response OK, results in changed data or fail."""
        template = Template.objects.get(name='test template')
        url = reverse('manage:template_edit', kwargs={'id': template.id})
        response = self.client.get(url)
        eq_(response.status_code, 200)
        response_ok = self.client.post(url, {
            'name': 'new name',
            'content': 'new content'
        })
        self.assertRedirects(response_ok, reverse('manage:templates'))
        template = Template.objects.get(id=template.id)
        eq_(template.content, 'new content')
        response_fail = self.client.post(url, {
            'name': 'no content'
        })
        eq_(response_fail.status_code, 200)

    def test_template_remove(self):
        template = Template.objects.get(name='test template')
        self._delete_test(template, 'manage:template_remove',
                          'manage:templates')

    def test_template_env_autofill(self):
        """The JSON autofiller responds correctly for the fixture template."""
        template = Template.objects.get(name='test template')
        response = self.client.get(reverse('manage:template_env_autofill'),
                                   {'template': template.id})
        eq_(response.status_code, 200)
        template_parsed = json.loads(response.content)
        ok_(template_parsed)
        eq_(template_parsed, {'variables': 'tv1=\ntv2='})


class TestApprovals(ManageTestCase):
    def test_approvals(self):
        event = Event.objects.get(title='Test event')
        group = Group.objects.get(name='testapprover')
        Approval.objects.create(event=event, group=group)

        response = self.client.get(reverse('manage:approvals'))
        eq_(response.status_code, 200)
        # if you access the approvals page without belonging to any group
        # you'll get a warning alert
        ok_('You are not a member of any group' in response.content)
        ok_('Test event' not in response.content)

        # belong to a group
        self.user.groups.add(group)
        response = self.client.get(reverse('manage:approvals'))
        eq_(response.status_code, 200)
        ok_('You are not a member of any group' not in response.content)
        ok_('Test event' in response.content)

        # but it shouldn't appear if it's removed
        event.status = Event.STATUS_REMOVED
        event.save()
        response = self.client.get(reverse('manage:approvals'))
        eq_(response.status_code, 200)
        ok_('Test event' not in response.content)

    def test_approval_review(self):
        event = Event.objects.get(title='Test event')
        group = Group.objects.get(name='testapprover')
        app = Approval.objects.create(event=event, group=group)

        url = reverse('manage:approval_review', kwargs={'id': app.id})
        response_not_in_group = self.client.get(url)
        self.assertRedirects(response_not_in_group,
                             reverse('manage:approvals'))
        User.objects.get(username='fake').groups.add(1)
        response = self.client.get(url)
        eq_(response.status_code, 200)
        response_approve = self.client.post(url, {'approve': 'approve'})
        self.assertRedirects(response_approve, reverse('manage:approvals'))
        app = Approval.objects.get(id=app.id)
        ok_(app.approved)
        ok_(app.processed)
        eq_(app.user, User.objects.get(username='fake'))


class TestLocations(ManageTestCase):
    def test_locations(self):
        """Location management pages return successfully."""
        response = self.client.get(reverse('manage:locations'))
        eq_(response.status_code, 200)

    def test_location_new(self):
        """Adding new location works correctly."""
        url = reverse('manage:location_new')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        response_ok = self.client.post(url, {
            'name': 'testing',
            'timezone': 'US/Pacific'
        })
        self.assertRedirects(response_ok, reverse('manage:locations'))
        location = Location.objects.get(name='testing')
        eq_(location.timezone, 'US/Pacific')
        response_fail = self.client.post(url)
        eq_(response_fail.status_code, 200)

    def test_location_remove(self):
        """Removing a location works correctly and leaves associated events
           with null locations."""
        location = Location.objects.get(id=1)
        self._delete_test(location, 'manage:location_remove',
                          'manage:locations')
        event = Event.objects.get(id=22)
        eq_(event.location, None)

    def test_location_edit(self):
        """Test location editor; timezone switch works correctly."""
        url = reverse('manage:location_edit', kwargs={'id': 1})
        response = self.client.get(url)
        eq_(response.status_code, 200)
        response_ok = self.client.post(url, {
            'name': 'eastern',
            'timezone': 'US/Eastern'
        })
        self.assertRedirects(response_ok, reverse('manage:locations'))
        location = Location.objects.get(id=1)
        eq_(location.timezone, 'US/Eastern')
        response_fail = self.client.post(url, {
            'name': 'eastern',
            'timezone': 'notatimezone'
        })
        eq_(response_fail.status_code, 200)

    def test_location_timezone(self):
        """Test timezone-ajax autofill."""
        url = reverse('manage:location_timezone')
        response_fail = self.client.get(url)
        eq_(response_fail.status_code, 404)
        response_fail = self.client.get(url, {'location': ''})
        eq_(response_fail.status_code, 404)
        response_fail = self.client.get(url, {'location': '23323'})
        eq_(response_fail.status_code, 404)
        response_ok = self.client.get(url, {'location': '1'})
        eq_(response_ok.status_code, 200)
        data = json.loads(response_ok.content)
        ok_('timezone' in data)
        eq_(data['timezone'], 'US/Pacific')


class TestTags(ManageTestCase):
    def test_tags(self):
        """Tag management pages return successfully."""
        response = self.client.get(reverse('manage:tags'))
        eq_(response.status_code, 200)

    def test_tag_remove(self):
        """Removing a tag works correctly and leaves associated events
           with null tags."""
        event = Event.objects.get(id=22)
        tag = Tag.objects.get(id=1)
        assert tag in event.tags.all()
        event.tags.add(Tag.objects.create(name='othertag'))
        eq_(event.tags.all().count(), 2)
        self._delete_test(tag, 'manage:tag_remove', 'manage:tags')
        event = Event.objects.get(id=22)
        eq_(event.tags.all().count(), 1)

    def test_tag_edit(self):
        """Test tag editor; timezone switch works correctly."""
        tag = Tag.objects.get(id=1)
        url = reverse('manage:tag_edit', kwargs={'id': 1})
        response = self.client.get(url)
        eq_(response.status_code, 200)
        response_ok = self.client.post(url, {
            'name': 'different',
        })
        self.assertRedirects(response_ok, reverse('manage:tags'))
        tag = Tag.objects.get(id=1)
        eq_(tag.name, 'different')

        Tag.objects.create(name='alreadyinuse')
        response_fail = self.client.post(url, {
            'name': 'ALREADYINUSE',
        })
        eq_(response_fail.status_code, 200)

        # repeat
        response_ok = self.client.post(url, {
            'name': 'different',
        })
        self.assertRedirects(response_ok, reverse('manage:tags'))

        # change it back
        response_ok = self.client.post(url, {
            'name': 'testing',
        })
        self.assertRedirects(response_ok, reverse('manage:tags'))


class TestManagementRoles(ManageTestCase):
    """Basic tests to ensure management roles / permissions are working."""
    fixtures = ['airmozilla/manage/tests/main_testdata.json',
                'airmozilla/manage/tests/manage_groups_testdata.json']

    def setUp(self):
        super(TestManagementRoles, self).setUp()
        self.user.is_superuser = False
        self.user.save()

    def _add_client_group(self, name):
        group = Group.objects.get(name=name)
        group.user_set.add(self.user)
        ok_(group in self.user.groups.all())

    def test_producer(self):
        """Producer can see fixture events and edit pages."""
        self._add_client_group('Producer')
        response_events = self.client.get(reverse('manage:events'))
        eq_(response_events.status_code, 200)
        ok_('Test event' in response_events.content)
        response_participants = self.client.get(reverse('manage:participants'))
        ok_(response_participants.status_code, 200)
        response_participant_edit = self.client.get(
            reverse('manage:participant_edit', kwargs={'id': 1})
        )
        eq_(response_participant_edit.status_code, 200)

    def _unprivileged_event_manager_tests(self, form_contains,
                                          form_not_contains):
        """Common tests for organizers/experienced organizers to ensure
           basic event/participant permissions are not violated."""
        response_event_request = self.client.get(
            reverse('manage:event_request')
        )
        eq_(response_event_request.status_code, 200)
        ok_(form_contains in response_event_request.content)
        ok_(form_not_contains not in response_event_request.content)
        response_events = self.client.get(reverse('manage:events'))
        eq_(response_events.status_code, 200)
        ok_('Test event' not in response_events.content,
            'Unprivileged viewer can see events which do not belong to it')
        event = Event.objects.get(title='Test event')
        event.creator = self.user
        event.save()
        response_events = self.client.get(reverse('manage:events'))
        ok_('Test event' in response_events.content,
            'Unprivileged viewer cannot see events which belong to it.')
        response_event_edit = self.client.get(reverse('manage:event_edit',
                                                      kwargs={'id': event.id}))
        ok_(form_contains in response_event_edit.content)
        ok_(form_not_contains not in response_event_edit.content)
        response_participants = self.client.get(reverse('manage:participants'))
        ok_(response_participants.status_code, 200)
        participant = Participant.objects.get(id=1)
        participant_edit_url = reverse('manage:participant_edit',
                                       kwargs={'id': participant.id})
        response_participant_edit_fail = self.client.get(participant_edit_url)
        self.assertRedirects(
            response_participant_edit_fail,
            reverse('manage:participants')
        )
        participant.creator = self.user
        participant.save()
        response_participant_edit_ok = self.client.get(participant_edit_url)
        eq_(response_participant_edit_ok.status_code, 200)

    def _unprivileged_page_tests(self, additional_pages=[]):
        """Common tests to ensure unprivileged admins do not have access to
           event or user configuration pages."""
        pages = additional_pages + [
            'manage:users',
            'manage:groups',
            'manage:categories',
            'manage:locations',
            'manage:templates'
        ]
        for page in pages:
            response = self.client.get(reverse(page))
            self.assertRedirects(response, settings.LOGIN_URL +
                                 '?next=' + reverse(page))

    def test_event_organizer(self):
        """Event organizer: ER with unprivileged form, can only edit own
           participants, can only see own events."""
        self._add_client_group('Event Organizer')
        self._unprivileged_event_manager_tests(
            form_contains='Time zone',  # EventRequestForm
            form_not_contains='Approvals'
        )
        self._unprivileged_page_tests(additional_pages=['manage:approvals'])

    def test_experienced_event_organizer(self):
        """Experienced event organizer: ER with semi-privileged form,
           can only edit own participants, can only see own events."""
        self._add_client_group('Experienced Event Organizer')
        self._unprivileged_event_manager_tests(
            form_contains='Approvals',  # EventExperiencedRequestForm
            form_not_contains='Featured'
        )
        self._unprivileged_page_tests(additional_pages=['manage:approvals'])

    def test_approver(self):
        """Approver (in this case, PR), can access the approval pages."""
        self._add_client_group('PR')
        self._unprivileged_page_tests(
            additional_pages=['manage:event_request', 'manage:events',
                              'manage:participants']
        )
        response_approvals = self.client.get(reverse('manage:approvals'))
        eq_(response_approvals.status_code, 200)


class TestFlatPages(ManageTestCase):
    def test_flatpages(self):
        response = self.client.get(reverse('manage:flatpages'))
        eq_(response.status_code, 200)

    def test_flatpage_new(self):
        url = reverse('manage:flatpage_new')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        response_ok = self.client.post(url, {
            'url': '/cool-page',
            'title': 'Cool title',
            'content': '<h4>Hello</h4>'
        })
        self.assertRedirects(response_ok, reverse('manage:flatpages'))
        flatpage = FlatPage.objects.get(url='/cool-page')
        ok_(flatpage)
        site, = flatpage.sites.all()
        eq_(site.pk, settings.SITE_ID)
        response_fail = self.client.post(url)
        eq_(response_fail.status_code, 200)

    def test_flatpage_edit(self):
        flatpage = FlatPage.objects.get(title='Test page')
        url = reverse('manage:flatpage_edit', kwargs={'id': flatpage.id})
        response = self.client.get(url)
        eq_(response.status_code, 200)
        response_ok = self.client.post(url, {
            'url': flatpage.url,
            'title': 'New test page',
            'content': '<p>New content</p>'
        })
        self.assertRedirects(response_ok, reverse('manage:flatpages'))
        flatpage = FlatPage.objects.get(id=flatpage.id)
        eq_(flatpage.content, '<p>New content</p>')
        response_fail = self.client.post(url, {
            'url': 'no title',
        })
        eq_(response_fail.status_code, 200)

    def test_flatpage_remove(self):
        flatpage = FlatPage.objects.get(title='Test page')
        self._delete_test(flatpage, 'manage:flatpage_remove',
                          'manage:flatpages')

    def test_view_flatpage(self):
        flatpage = FlatPage.objects.get(title='Test page')
        response = self.client.get('/pages%s' % flatpage.url)
        eq_(response.status_code, 200)
        ok_('Test page' in response.content)

    def test_flatpage_new_with_sidebar(self):
        url = reverse('manage:flatpage_new')
        # not split by at least 2 `_`
        response_fail = self.client.post(url, {
            'url': 'sidebar_incorrectformat',
            'title': 'whatever',
            'content': '<h4>Hello</h4>'
        })
        eq_(response_fail.status_code, 200)
        ok_('Form errors!' in response_fail.content)

        # unrecognized slug
        response_fail = self.client.post(url, {
            'url': 'sidebar_east_never_heard_of',
            'title': 'whatever',
            'content': '<h4>Hello</h4>'
        })
        eq_(response_fail.status_code, 200)
        ok_('Form errors!' in response_fail.content)

        Channel.objects.create(
            name='Heard Of',
            slug='heard_of'
        )

        # should work now
        response_ok = self.client.post(url, {
            'url': 'sidebar_east_heard_of',
            'title': 'whatever',
            'content': '<h4>Hello</h4>'
        })
        self.assertRedirects(response_ok, reverse('manage:flatpages'))

        flatpage = FlatPage.objects.get(
            url='sidebar_east_heard_of'
        )
        # the title would automatically become auto generated
        ok_('Heard Of' in flatpage.title)

    def test_flatpage_edit_with_sidebar(self):
        flatpage = FlatPage.objects.get(title='Test page')
        url = reverse('manage:flatpage_edit', kwargs={'id': flatpage.id})
        response = self.client.get(url)
        eq_(response.status_code, 200)
        response_ok = self.client.post(url, {
            'url': 'sidebar_bottom_main',
            'title': 'New test page',
            'content': '<p>New content</p>'
        })
        self.assertRedirects(response_ok, reverse('manage:flatpages'))
        flatpage = FlatPage.objects.get(id=flatpage.id)
        eq_(flatpage.content, '<p>New content</p>')
        eq_('Sidebar (bottom) Main', flatpage.title)

    def test_flatpage_with_url_that_clashes(self):
        event = Event.objects.get(slug='test-event')
        FlatPage.objects.create(
            url='/' + event.slug,
            title='Some Page',
        )
        response = self.client.get(reverse('manage:flatpages'))
        eq_(response.status_code, 200)
        # there should now be a link to event it clashes with
        ok_('/pages/%s' % event.slug in response.content)
        event_url = reverse('main:event', args=(event.slug,))
        ok_(event_url in response.content)


class TestErrorAlerts(ManageTestCase):

    def test_new_template_with_error(self):
        url = reverse('manage:template_new')
        response = self.client.get(url)
        ok_('Form errors!' not in response.content)
        response = self.client.post(url, {
            'name': '',
            'content': 'hello!'
        })
        ok_('Form errors!' in response.content)


class TestSuggestions(ManageTestCase):

    placeholder = 'airmozilla/manage/tests/firefox.png'

    def test_suggestions_page(self):
        bob = User.objects.create_user('bob', email='bob@mozilla.com')
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        tomorrow = now + datetime.timedelta(days=1)
        location = Location.objects.get(id=1)
        category = Category.objects.create(name='CATEGORY')
        SuggestedEvent.objects.create(
            user=bob,
            title='TITLE',
            slug='SLUG',
            short_description='SHORT DESCRIPTION',
            description='DESCRIPTION',
            start_time=tomorrow,
            location=location,
            category=category,
            placeholder_img=self.placeholder,
            privacy=Event.PRIVACY_CONTRIBUTORS,
            submitted=now,
        )
        SuggestedEvent.objects.create(
            user=bob,
            title='TITLE2',
            slug='SLUG2',
            short_description='SHORT DESCRIPTION2',
            description='DESCRIPTION2',
            start_time=tomorrow,
            location=location,
            category=category,
            placeholder_img=self.placeholder,
            privacy=Event.PRIVACY_CONTRIBUTORS,
            submitted=now - datetime.timedelta(days=1),
        )
        url = reverse('manage:suggestions')
        response = self.client.get(url)
        eq_(response.status_code, 200)

    def test_approve_suggested_event_basic(self):
        bob = User.objects.create_user('bob', email='bob@mozilla.com')
        location = Location.objects.get(id=1)
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        tomorrow = now + datetime.timedelta(days=1)
        category = Category.objects.create(name='CATEGORY')
        tag1 = Tag.objects.create(name='TAG1')
        tag2 = Tag.objects.create(name='TAG2')
        channel = Channel.objects.create(name='CHANNEL')

        # create a suggested event that has everything filled in
        event = SuggestedEvent.objects.create(
            user=bob,
            title='TITLE' * 10,
            slug='SLUG',
            short_description='SHORT DESCRIPTION',
            description='DESCRIPTION',
            start_time=tomorrow,
            location=location,
            category=category,
            placeholder_img=self.placeholder,
            privacy=Event.PRIVACY_CONTRIBUTORS,
            #call_info='CALL INFO',
            additional_links='ADDITIONAL LINKS',
            remote_presenters='RICHARD & ZANDR',
            submitted=now,
        )
        event.tags.add(tag1)
        event.tags.add(tag2)
        event.channels.add(channel)

        url = reverse('manage:suggestion_review', args=(event.pk,))
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('TITLE' in response.content)
        ok_('SLUG' in response.content)
        ok_('SHORT DESCRIPTION' in response.content)
        ok_('DESCRIPTION' in response.content)
        ok_('ADDITIONAL LINKS' in response.content)
        ok_('RICHARD &amp; ZANDR' in response.content)
        ok_(os.path.basename(self.placeholder) in response.content)
        ok_(category.name in response.content)
        ok_(location.name in response.content)
        ok_(event.get_privacy_display() in response.content)
        #ok_('CALL INFO' in response.content

        response = self.client.post(url)
        eq_(response.status_code, 302)

        # re-load it
        event = SuggestedEvent.objects.get(pk=event.pk)
        real = event.accepted
        assert real
        eq_(real.title, event.title)
        eq_(real.slug, event.slug)
        eq_(real.short_description, event.short_description)
        eq_(real.description, event.description)
        eq_(real.placeholder_img, event.placeholder_img)
        eq_(real.category, category)
        eq_(real.location, location)
        eq_(real.start_time, event.start_time)
        eq_(real.privacy, event.privacy)
        eq_(real.additional_links, event.additional_links)
        eq_(real.remote_presenters, event.remote_presenters)
        assert real.tags.all()
        eq_([x.name for x in real.tags.all()],
            [x.name for x in event.tags.all()])
        assert real.channels.all()
        eq_([x.name for x in real.channels.all()],
            [x.name for x in event.channels.all()])

        # it should have sent an email back
        email_sent = mail.outbox[-1]
        ok_(email_sent.recipients(), ['bob@mozilla.com'])
        ok_('accepted' in email_sent.subject)
        ok_('TITLE' in email_sent.subject)
        ok_('TITLE' in email_sent.body)

    def test_reject_suggested_event(self):
        bob = User.objects.create_user('bob', email='bob@mozilla.com')
        location = Location.objects.get(id=1)
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        tomorrow = now + datetime.timedelta(days=1)
        category = Category.objects.create(name='CATEGORY')
        tag1 = Tag.objects.create(name='TAG1')
        tag2 = Tag.objects.create(name='TAG2')
        channel = Channel.objects.create(name='CHANNEL')

        # create a suggested event that has everything filled in
        event = SuggestedEvent.objects.create(
            user=bob,
            title='TITLE',
            slug='SLUG',
            short_description='SHORT DESCRIPTION',
            description='DESCRIPTION',
            start_time=tomorrow,
            location=location,
            category=category,
            placeholder_img=self.placeholder,
            privacy=Event.PRIVACY_CONTRIBUTORS,
            #call_info='CALL INFO',
            #additional_links='ADDITIONAL LINKS',
            submitted=now,
        )
        event.tags.add(tag1)
        event.tags.add(tag2)
        event.channels.add(channel)

        url = reverse('manage:suggestion_review', args=(event.pk,))
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('TITLE' in response.content)
        ok_('SLUG' in response.content)
        ok_('SHORT DESCRIPTION' in response.content)
        ok_('DESCRIPTION' in response.content)
        ok_(os.path.basename(self.placeholder) in response.content)
        ok_(category.name in response.content)
        ok_(location.name in response.content)
        ok_(event.get_privacy_display() in response.content)
        #ok_('CALL INFO' in response.content
        #ok_('ADDITIONAL LINKS' in response.content)

        data = {'reject': 'true'}
        response = self.client.post(url, data)
        eq_(response.status_code, 200)

        data['review_comments'] = 'You suck!'
        response = self.client.post(url, data)
        eq_(response.status_code, 302)

        # re-load it
        event = SuggestedEvent.objects.get(pk=event.pk)
        ok_(not event.accepted)
        ok_(not event.submitted)

        # it should have sent an email back
        email_sent = mail.outbox[-1]
        ok_(email_sent.recipients(), ['bob@mozilla.com'])
        ok_('not accepted' in email_sent.subject)
        ok_('TITLE' in email_sent.body)
        ok_('You suck!' in email_sent.body)
        summary_url = reverse('suggest:summary', args=(event.pk,))
        ok_(summary_url in email_sent.body)

    def test_comment_suggested_event(self):
        bob = User.objects.create_user('bob', email='bob@mozilla.com')
        location = Location.objects.get(id=1)
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        tomorrow = now + datetime.timedelta(days=1)
        category = Category.objects.create(name='CATEGORY')
        tag1 = Tag.objects.create(name='TAG1')
        tag2 = Tag.objects.create(name='TAG2')
        channel = Channel.objects.create(name='CHANNEL')

        # create a suggested event that has everything filled in
        event = SuggestedEvent.objects.create(
            user=bob,
            title='TITLE',
            slug='SLUG',
            short_description='SHORT DESCRIPTION',
            description='DESCRIPTION',
            start_time=tomorrow,
            location=location,
            category=category,
            placeholder_img=self.placeholder,
            privacy=Event.PRIVACY_CONTRIBUTORS,
            #call_info='CALL INFO',
            #additional_links='ADDITIONAL LINKS',
            submitted=now,
        )
        event.tags.add(tag1)
        event.tags.add(tag2)
        event.channels.add(channel)

        url = reverse('manage:suggestion_review', args=(event.pk,))
        data = {
            'save_comment': 1,
            'comment': ''
        }
        response = self.client.post(url, data)
        eq_(response.status_code, 200)
        ok_('This field is required' in response.content)
        assert not SuggestedEventComment.objects.all()

        data['comment'] = """
        Hi!
        <script>alert("xss")</script>
        """
        response = self.client.post(url, data)
        eq_(response.status_code, 302)
        comment, = SuggestedEventComment.objects.all()
        eq_(comment.comment, data['comment'].strip())
        eq_(comment.user, self.user)  # who I'm logged in as

        # this should have sent an email to bob
        email_sent = mail.outbox[-1]
        ok_(email_sent.recipients(), [bob.email])
        ok_('New comment' in email_sent.subject)
        ok_(event.title in email_sent.subject)
        ok_('<script>alert("xss")</script>' in email_sent.body)
        ok_(reverse('suggest:summary', args=(event.pk,)) in email_sent.body)


class TestEventTweets(ManageTestCase):

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

    @mock.patch('urllib.urlopen')
    def test_prepare_new_tweet(self, p_urlopen):

        def mocked_read():
            r = {
                u'status_code': 200,
                u'data': {
                    u'url': u'http://mzl.la/1adh2wT',
                    u'hash': u'1adh2wT',
                    u'global_hash': u'1adh2wU',
                    u'long_url': u'https://air.mozilla.org/it-buildout/',
                    u'new_hash': 0
                },
                u'status_txt': u'OK'
            }
            return json.dumps(r)

        p_urlopen().read.side_effect = mocked_read

        event = Event.objects.get(title='Test event')
        # the event must have a real placeholder image
        with open(self.placeholder) as fp:
            response = self.client.post(
                reverse('manage:event_edit', args=(event.pk,)),
                dict(self.event_base_data,
                     title=event.title,
                     short_description="Check out <b>This!</b>",
                     description="Something longer",
                     placeholder_img=fp)
            )
            assert response.status_code == 302, response.status_code

        # on the edit page, there should be a link
        response = self.client.get(
            reverse('manage:event_edit', args=(event.pk,))
        )
        assert response.status_code == 200
        url = reverse('manage:new_event_tweet', args=(event.pk,))
        ok_(url in response.content)

        response = self.client.get(url)
        eq_(response.status_code, 200)
        textarea = (
            response.content
            .split('<textarea')[1]
            .split('>')[1]
            .split('</textarea')[0]
        )
        ok_(textarea.startswith('Check out This!'))
        event = Event.objects.get(pk=event.pk)
        event_url = 'http://testserver'
        event_url += reverse('main:event', args=(event.slug,))
        ok_('http://mzl.la/1adh2wT' in textarea)
        ok_(event_url not in textarea)

        # try to submit it with longer than 140 characters
        response = self.client.post(url, {
            'text': 'x' * 141,
            'include_placeholder': True,
        })
        eq_(response.status_code, 200)
        assert not EventTweet.objects.all().count()
        ok_('it has 141' in response.content)

        # try again
        response = self.client.post(url, {
            'text': 'Bla bla #tag',
            'include_placeholder': True,
        })
        eq_(response.status_code, 302)
        ok_(EventTweet.objects.all().count())
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        event_tweet, = EventTweet.objects.all()
        _fmt = '%Y%m%d%H%M'
        eq_(
            event_tweet.send_date.strftime(_fmt),
            now.strftime(_fmt)
        )
        ok_(not event_tweet.sent_date)
        ok_(not event_tweet.error)
        ok_(not event_tweet.tweet_id)

    def test_event_tweets_empty(self):
        event = Event.objects.get(title='Test event')
        url = reverse('manage:event_tweets', args=(event.pk,))
        response = self.client.get(url)
        eq_(response.status_code, 200)

    def test_event_tweets_states(self):
        event = Event.objects.get(title='Test event')
        assert event in Event.objects.approved()
        group = Group.objects.get(name='testapprover')
        Approval.objects.create(
            event=event,
            group=group,
        )
        assert event not in Event.objects.approved()
        url = reverse('manage:event_tweets', args=(event.pk,))
        response = self.client.get(url)
        eq_(response.status_code, 200)

        tweet = EventTweet.objects.create(
            event=event,
            text='Bla bla',
            send_date=datetime.datetime.utcnow().replace(tzinfo=utc),
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('Bla bla' in response.content)
        ok_('Needs to be approved first' in response.content)
        from airmozilla.main.helpers import js_date
        ok_(
            js_date(tweet.send_date.replace(microsecond=0))
            not in response.content
        )

        # also check that 'Bla bla' is shown on the Edit Event page
        edit_url = reverse('manage:event_edit', args=(event.pk,))
        response = self.client.get(edit_url)
        eq_(response.status_code, 200)
        ok_('Bla bla' in response.content)

        tweet.tweet_id = '1234567890'
        tweet.sent_date = (
            datetime.datetime.utcnow().replace(tzinfo=utc)
            - datetime.timedelta(days=1)
        )
        tweet.save()

        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('Bla bla' in response.content)
        ok_(
            'https://twitter.com/%s/status/1234567890'
            % settings.TWITTER_USERNAME
            in response.content
        )
        ok_(
            js_date(tweet.sent_date.replace(microsecond=0))
            in response.content
        )

        tweet.tweet_id = None
        tweet.error = "Some error"
        tweet.save()
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('Bla bla' in response.content)
        ok_(
            'https://twitter.com/%s/status/1234567890'
            % settings.TWITTER_USERNAME
            not in response.content
        )
        ok_(
            js_date(tweet.sent_date.replace(microsecond=0))
            in response.content
        )
        ok_('Failed to send' in response.content)

    def test_all_event_tweets_states(self):
        event = Event.objects.get(title='Test event')
        assert event in Event.objects.approved()
        group = Group.objects.get(name='testapprover')
        Approval.objects.create(
            event=event,
            group=group,
        )
        assert event not in Event.objects.approved()
        url = reverse('manage:all_event_tweets')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        tweet = EventTweet.objects.create(
            event=event,
            text='Bla bla',
            send_date=datetime.datetime.utcnow().replace(tzinfo=utc),
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('Bla bla' in response.content)
        ok_('Needs to be approved first' in response.content)
        from airmozilla.main.helpers import js_date
        ok_(
            js_date(tweet.send_date.replace(microsecond=0))
            not in response.content
        )

        # also check that 'Bla bla' is shown on the Edit Event page
        edit_url = reverse('manage:event_edit', args=(event.pk,))
        response = self.client.get(edit_url)
        eq_(response.status_code, 200)
        ok_('Bla bla' in response.content)

        tweet.tweet_id = '1234567890'
        tweet.sent_date = (
            datetime.datetime.utcnow().replace(tzinfo=utc)
            - datetime.timedelta(days=1)
        )
        tweet.save()

        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('Bla bla' in response.content)
        ok_(
            'https://twitter.com/%s/status/1234567890'
            % settings.TWITTER_USERNAME
            in response.content
        )
        ok_(
            js_date(tweet.sent_date.replace(microsecond=0))
            in response.content
        )

        tweet.tweet_id = None
        tweet.error = "Some error"
        tweet.save()
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('Bla bla' in response.content)
        ok_(
            'https://twitter.com/%s/status/1234567890'
            % settings.TWITTER_USERNAME
            not in response.content
        )
        ok_(
            js_date(tweet.sent_date.replace(microsecond=0))
            in response.content
        )
        ok_('Failed to send' in response.content)

    @mock.patch('airmozilla.manage.views.send_tweet')
    def test_force_send_now(self, mocked_send_tweet):
        event = Event.objects.get(title='Test event')

        tweet = EventTweet.objects.create(
            event=event,
            text='Bla bla',
            send_date=datetime.datetime.utcnow().replace(tzinfo=utc),
        )

        def mock_send_tweet(event_tweet):
            event_tweet.tweet_id = '1234567890'
            event_tweet.save()
        mocked_send_tweet.side_effect = mock_send_tweet

        url = reverse('manage:event_tweets', args=(event.pk,))
        response = self.client.post(url, {
            'send': tweet.pk,
        })
        eq_(response.status_code, 302)
        tweet = EventTweet.objects.get(pk=tweet.pk)
        eq_(tweet.tweet_id, '1234567890')

    def test_view_tweet_error(self):
        event = Event.objects.get(title='Test event')

        tweet = EventTweet.objects.create(
            event=event,
            text='Bla bla',
            send_date=datetime.datetime.utcnow().replace(tzinfo=utc),
            error='Crap!'
        )
        url = reverse('manage:event_tweets', args=(event.pk,))
        response = self.client.post(url, {
            'error': tweet.pk,
        })
        eq_(response.status_code, 200)
        eq_(response['content-type'], 'text/plain')
        ok_('Crap!' in response.content)

    def test_cancel_event_tweet(self):
        event = Event.objects.get(title='Test event')

        tweet = EventTweet.objects.create(
            event=event,
            text='Bla bla',
            send_date=datetime.datetime.utcnow().replace(tzinfo=utc),
        )

        url = reverse('manage:event_tweets', args=(event.pk,))
        response = self.client.post(url, {
            'cancel': tweet.pk,
        })
        eq_(response.status_code, 302)
        ok_(not EventTweet.objects.all().count())

    def test_create_event_tweet_with_location_timezone(self):
        location = Location.objects.create(
            name='Paris',
            timezone='Europe/Paris'
        )
        event = Event.objects.get(title='Test event')
        event.location = location
        event.save()

        # the event must have a real placeholder image
        with open(self.placeholder) as fp:
            response = self.client.post(
                reverse('manage:event_edit', args=(event.pk,)),
                dict(self.event_base_data,
                     title=event.title,
                     short_description="Check out <b>This!</b>",
                     description="Something longer",
                     placeholder_img=fp)
            )
            assert response.status_code == 302, response.status_code

        url = reverse('manage:new_event_tweet', args=(event.pk,))
        now = datetime.datetime.utcnow()
        response = self.client.post(url, {
            'text': 'Bla bla #tag',
            'include_placeholder': True,
            'send_date': now.strftime('%Y-%m-%d 12:00'),
        })
        eq_(response.status_code, 302)
        event_tweet, = EventTweet.objects.all()
        # we specified it as noon in Paris, but the save time
        # will be UTC
        ok_(event_tweet.send_date.hour != 12)
        assert event_tweet.send_date.strftime('%Z') == 'UTC'


class TestVidlyMedia(ManageTestCase):

    def tearDown(self):
        super(TestVidlyMedia, self).tearDown()
        cache.clear()

    def test_vidly_media(self):
        url = reverse('manage:vidly_media')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        event = Event.objects.get(title='Test event')
        ok_(event.title not in response.content)

        event.template = Template.objects.create(
            name='Vid.ly Something',
            content='<iframe>'
        )
        event.save()

        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_(event.title in response.content)

        # or the event might not yet have made the switch but already
        # has a VidlySubmission
        event.template = None
        event.save()

        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_(event.title not in response.content)

        VidlySubmission.objects.create(
            event=event,
            tag='xyz000'
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_(event.title in response.content)

    @mock.patch('urllib2.urlopen')
    def test_vidly_media_with_status(self, p_urlopen):

        def mocked_urlopen(request):
            return StringIO(SAMPLE_MEDIALIST_XML.strip())

        p_urlopen.side_effect = mocked_urlopen

        url = reverse('manage:vidly_media')
        response = self.client.get(url, {'status': 'Error'})
        eq_(response.status_code, 200)

        event = Event.objects.get(title='Test event')
        ok_(event.title not in response.content)

        event.template = Template.objects.create(
            name='Vid.ly Something',
            content='<iframe>'
        )
        event.template_environment = {'tag': 'abc123'}
        event.save()

        response = self.client.get(url, {'status': 'Error'})
        eq_(response.status_code, 200)
        ok_(event.title in response.content)

    @mock.patch('urllib2.urlopen')
    def test_vidly_media_status(self, p_urlopen):

        def mocked_urlopen(request):
            return StringIO(SAMPLE_XML.strip())

        p_urlopen.side_effect = mocked_urlopen

        event = Event.objects.get(title='Test event')
        url = reverse('manage:vidly_media_status')
        response = self.client.get(url)
        eq_(response.status_code, 400)

        event.template = Template.objects.create(
            name='Vid.ly Something',
            content='<iframe>'
        )
        event.template_environment = {'tag': 'abc123'}
        event.save()

        response = self.client.get(url, {'id': 9999})
        eq_(response.status_code, 404)

        response = self.client.get(url, {'id': event.pk})
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data['status'], 'Finished')

    @mock.patch('urllib2.urlopen')
    def test_vidly_media_status_not_vidly_template(self, p_urlopen):

        def mocked_urlopen(request):
            return StringIO(SAMPLE_XML.strip())

        p_urlopen.side_effect = mocked_urlopen

        event = Event.objects.get(title='Test event')
        url = reverse('manage:vidly_media_status')
        response = self.client.get(url)
        eq_(response.status_code, 400)

        event.template = Template.objects.create(
            name='EdgeCast',
            content='<iframe>'
        )
        event.template_environment = {'other': 'stuff'}
        event.save()

        VidlySubmission.objects.create(
            event=event,
            tag='abc123'
        )

        response = self.client.get(url, {'id': event.pk})
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data['status'], 'Finished')

    @mock.patch('urllib2.urlopen')
    def test_vidly_media_info(self, p_urlopen):

        sent_queries = []

        def mocked_urlopen(request):
            sent_queries.append(True)
            return StringIO(SAMPLE_XML.strip())

        p_urlopen.side_effect = mocked_urlopen

        event = Event.objects.get(title='Test event')
        url = reverse('manage:vidly_media_info')
        response = self.client.get(url)
        eq_(response.status_code, 400)

        event.template = Template.objects.create(
            name='Vid.ly Something',
            content='<iframe>'
        )
        event.template_environment = {'foo': 'bar'}
        event.save()

        response = self.client.get(url, {'id': 9999})
        eq_(response.status_code, 404)

        response = self.client.get(url, {'id': event.pk})
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        fields = data['fields']
        ok_([x for x in fields if x['key'] == '*Note*'])

        event.template_environment = {'tag': 'abc123'}
        event.save()

        response = self.client.get(url, {'id': event.pk})
        eq_(response.status_code, 200)
        eq_(len(sent_queries), 1)

        data = json.loads(response.content)
        fields = data['fields']
        ok_(
            [x for x in fields
             if x['key'] == 'Status' and x['value'] == 'Finished']
        )

        # a second time and it should be cached
        response = self.client.get(url, {'id': event.pk})
        eq_(response.status_code, 200)
        eq_(len(sent_queries), 1)

        # unless you set this
        response = self.client.get(url, {'id': event.pk, 'refresh': 1})
        eq_(response.status_code, 200)
        eq_(len(sent_queries), 2)

    @mock.patch('urllib2.urlopen')
    def test_vidly_media_info_with_error(self, p_urlopen):

        sent_queries = []

        def mocked_urlopen(request):
            sent_queries.append(True)
            return StringIO(SAMPLE_INVALID_LINKS_XML.strip())

        p_urlopen.side_effect = mocked_urlopen

        event = Event.objects.get(title='Test event')
        url = reverse('manage:vidly_media_info')
        response = self.client.get(url)
        eq_(response.status_code, 400)

        event.template = Template.objects.create(
            name='Vid.ly Something',
            content='<iframe>'
        )
        event.template_environment = {'tag': 'abc123'}
        event.save()

        response = self.client.get(url, {'id': event.pk})
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data['ERRORS'], ['Tag (abc123) not found in Vid.ly'])

    @mock.patch('urllib2.urlopen')
    def test_vidly_media_info_with_past_submission_info(self, p_urlopen):

        def mocked_urlopen(request):
            return StringIO(SAMPLE_XML.strip())

        p_urlopen.side_effect = mocked_urlopen

        event = Event.objects.get(title='Test event')
        url = reverse('manage:vidly_media_info')

        event.template = Template.objects.create(
            name='Vid.ly Something',
            content='<iframe>'
        )
        event.template_environment = {'tag': 'abc123'}
        event.save()

        response = self.client.get(url, {
            'id': event.pk,
        })
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        ok_(data['fields'])
        ok_(data['past_submission'])
        eq_(
            data['past_submission']['url'],
            'http://videos.mozilla.org/bla.f4v'
        )
        eq_(
            data['past_submission']['email'],
            'airmozilla@mozilla.com'
        )
        previous_past_submission = data['past_submission']

        response = self.client.get(url, {
            'id': event.pk,
            'past_submission_info': True
        })
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        ok_(data['fields'])
        ok_(data['past_submission'])
        eq_(previous_past_submission, data['past_submission'])

        submission = VidlySubmission.objects.create(
            event=event,
            url='http://something.com',
            hd=True,
            token_protection=True,
            email='test@example.com'
        )
        response = self.client.get(url, {
            'id': event.pk,
            'past_submission_info': True
        })
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        past = data['past_submission']
        eq_(past['url'], submission.url)
        eq_(past['email'], submission.email)
        ok_(submission.hd)
        ok_(submission.token_protection)

    @mock.patch('urllib2.urlopen')
    def test_vidly_media_status_with_caching(self, p_urlopen):

        sent_queries = []

        def mocked_urlopen(request):
            sent_queries.append(True)
            return StringIO(SAMPLE_XML.strip())

        p_urlopen.side_effect = mocked_urlopen

        event = Event.objects.get(title='Test event')
        url = reverse('manage:vidly_media_status')

        event.template = Template.objects.create(
            name='Vid.ly Something',
            content='<iframe>'
        )
        event.template_environment = {'foo': 'bar'}
        event.save()

        response = self.client.get(url, {'id': event.pk})
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data, {})
        eq_(len(sent_queries), 0)

        event.template_environment = {'tag': 'abc123'}
        event.save()

        response = self.client.get(url, {'id': event.pk})
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data, {'status': 'Finished'})
        eq_(len(sent_queries), 1)

        # do it again, it should be cached
        response = self.client.get(url, {'id': event.pk})
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data, {'status': 'Finished'})
        eq_(len(sent_queries), 1)

        response = self.client.get(url, {'id': event.pk, 'refresh': 'true'})
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data, {'status': 'Finished'})
        eq_(len(sent_queries), 2)

    @mock.patch('urllib2.urlopen')
    def test_vidly_media_resubmit(self, p_urlopen):

        sent_queries = []

        def mocked_urlopen(request):
            sent_queries.append(True)
            if 'AddMedia' in request.data:
                return StringIO("""
                <?xml version="1.0"?>
                <Response>
                  <Message>All medias have been added.</Message>
                  <MessageCode>2.1</MessageCode>
                  <BatchID>47520</BatchID>
                  <Success>
                    <MediaShortLink>
                      <SourceFile>http://www.com/file.flv</SourceFile>
                      <ShortLink>8oxv6x</ShortLink>
                      <MediaID>13969839</MediaID>
                      <QRCode>http://vid.ly/8oxv6x/qrcodeimg</QRCode>
                      <HtmlEmbed>code code</HtmlEmbed>
                      <EmailEmbed>more code code</EmailEmbed>
                    </MediaShortLink>
                  </Success>
                </Response>
                """.strip())
            elif 'DeleteMedia' in request.data:
                return StringIO("""
                <?xml version="1.0"?>
                <Response>
                  <Message>Success</Message>
                  <MessageCode>0.0</MessageCode>
                  <Success>
                    <MediaShortLink>8oxv6x</MediaShortLink>
                  </Success>
                  <Errors>
                    <Error>
                      <SourceFile>http://www.com</SourceFile>
                      <ErrorCode>1</ErrorCode>
                      <Description>ErrorDescriptionK</Description>
                      <Suggestion>ErrorSuggestionK</Suggestion>
                    </Error>
                  </Errors>
                </Response>
                """.strip())
            else:
                raise NotImplementedError(request.data)

        p_urlopen.side_effect = mocked_urlopen

        event = Event.objects.get(title='Test event')
        event.privacy = Event.PRIVACY_COMPANY
        url = reverse('manage:vidly_media_resubmit')

        event.template = Template.objects.create(
            name='Vid.ly Something',
            content='<iframe>'
        )
        event.template_environment = {'tag': 'abc123'}
        event.save()

        response = self.client.post(url, {
            'id': event.pk,
        })
        eq_(response.status_code, 200)
        ok_('errorlist' in response.content)

        ok_(not VidlySubmission.objects.filter(event=event))

        response = self.client.post(url, {
            'id': event.pk,
            'url': 'http://better.com',
            'email': 'peter@example.com',
            'hd': True,
            'token_protection': False,  # observe!
        })
        eq_(response.status_code, 302)

        submission, = VidlySubmission.objects.filter(event=event)
        ok_(submission.url, 'http://better.com')
        ok_(submission.email, 'peter@example.com')
        ok_(submission.hd)
        # this gets forced on since the event is not public
        ok_(submission.token_protection)

        event = Event.objects.get(pk=event.pk)
        eq_(event.template_environment['tag'], '8oxv6x')

    @mock.patch('urllib2.urlopen')
    def test_vidly_media_resubmit_with_error(self, p_urlopen):

        def mocked_urlopen(request):
            if 'AddMedia' in request.data:
                return StringIO("""
                <?xml version="1.0"?>
            <Response>
              <Message>Error</Message>
              <MessageCode>0.0</MessageCode>
              <Errors>
                <Error>
                  <ErrorCode>0.0</ErrorCode>
                  <ErrorName>Error message</ErrorName>
                  <Description>bla bla</Description>
                  <Suggestion>ble ble</Suggestion>
                </Error>
              </Errors>
            </Response>
                """.strip())
            else:
                raise NotImplementedError(request.data)

        p_urlopen.side_effect = mocked_urlopen

        event = Event.objects.get(title='Test event')
        url = reverse('manage:vidly_media_resubmit')

        event.template = Template.objects.create(
            name='Vid.ly Something',
            content='<iframe>'
        )
        event.template_environment = {'tag': 'abc123'}
        event.save()

        response = self.client.post(url, {
            'id': event.pk,
            'url': 'http://better.com',
            'email': 'peter@example.com',
            'hd': True
        })
        eq_(response.status_code, 302)

        submission, = VidlySubmission.objects.filter(event=event)
        ok_(submission.url, 'http://better.com')
        ok_(submission.email, 'peter@example.com')
        ok_(submission.hd)
        ok_(not submission.token_protection)
        ok_(submission.submission_error)
        ok_('ble ble' in submission.submission_error)

        event = Event.objects.get(pk=event.pk)
        eq_(event.template_environment['tag'], 'abc123')  # the old one


class TestURLTransforms(ManageTestCase):

    @override_settings(URL_TRANSFORM_PASSWORDS={'foo': 'secret'})
    def test_url_transforms(self):
        url = reverse('manage:url_transforms')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        def quote(x):
            return x.replace("'", '&#39;')

        ok_(quote("{{ password('foo') }}") in response.content)

        # now with some matchers in there
        match = URLMatch.objects.create(
            name="Secure Things",
            string='secure'
        )
        URLTransform.objects.create(
            match=match,
            find='^secure',
            replace_with='insecure'
        )
        response = self.client.get(url)
        eq_(response.status_code, 200)
        ok_('Secure Things' in response.content)

    def test_url_match_new(self):
        url = reverse('manage:url_match_new')
        response = self.client.get(url)
        eq_(response.status_code, 200)

        response = self.client.post(url, {
            'name': 'Secure Things',
            'string': '^secure$'
        })
        self.assertRedirects(response, reverse('manage:url_transforms'))
        ok_(URLMatch.objects.get(string='^secure$'))

    def test_url_match_remove(self):
        match = URLMatch.objects.create(
            name="Secure Things",
            string='secure'
        )
        URLTransform.objects.create(
            match=match,
            find='^secure',
            replace_with='insecure'
        )
        eq_(URLMatch.objects.all().count(), 1)
        eq_(URLTransform.objects.all().count(), 1)

        url = reverse('manage:url_match_remove', args=(match.pk,))
        response = self.client.post(url)
        self.assertRedirects(response, reverse('manage:url_transforms'))

        eq_(URLMatch.objects.all().count(), 0)
        eq_(URLTransform.objects.all().count(), 0)

    def test_url_match_run(self):
        match = URLMatch.objects.create(
            name="Secure Things",
            string='secure'
        )
        URLTransform.objects.create(
            match=match,
            find='secure',
            replace_with='insecure'
        )
        url = reverse('manage:url_match_run')
        response = self.client.get(url, {
            'url': 'http://www.secure.com'
        })
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        ok_(not data['error'])
        eq_(data['result'], 'http://www.insecure.com')

    def test_url_tranform_add(self):
        match = URLMatch.objects.create(
            name="Secure Things",
            string='secure'
        )
        url = reverse('manage:url_transform_add', args=(match.pk,))
        response = self.client.post(url, {
            'find': 'secure',
            'replace_with': 'insecure'
        })
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        ok_(data['transform']['id'])

        ok_(
            URLTransform.objects.get(
                match=match,
                find='secure',
                replace_with='insecure'
            )
        )

    def test_url_tranform_edit(self):
        match = URLMatch.objects.create(
            name="Secure Things",
            string='secure'
        )
        transform = URLTransform.objects.create(
            match=match,
            find='secure',
            replace_with='insecure'
        )
        url = reverse('manage:url_transform_edit',
                      args=(match.pk, transform.pk))
        response = self.client.post(url, {
            'find': 'insecure',
            'replace_with': 'secure'
        })
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data, True)

        ok_(
            URLTransform.objects.get(
                match=match,
                find='insecure',
                replace_with='secure'
            )
        )

    def test_url_tranform_remove(self):
        match = URLMatch.objects.create(
            name="Secure Things",
            string='secure'
        )
        transform = URLTransform.objects.create(
            match=match,
            find='secure',
            replace_with='insecure'
        )
        url = reverse('manage:url_transform_remove',
                      args=(match.pk, transform.pk))
        response = self.client.post(url)
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data, True)
        eq_(URLTransform.objects.all().count(), 0)
