import logging
import urllib
import json
import requests
from django.conf import settings


class BadStatusCodeError(Exception):
    pass


def _fetch_users(email, groups=None):
    if not getattr(settings, 'MOZILLIANS_API_KEY', None):  # pragma no cover
        logging.warning("'MOZILLIANS_API_KEY' not set up.")
        return False

    # /api/v1/users/?app_name=foobar&app_key=12345&email=test@example.com
    url = settings.MOZILLIANS_API_BASE + '/api/v1/users/'
    data = {
        'app_name': settings.MOZILLIANS_API_APPNAME,
        'app_key': settings.MOZILLIANS_API_KEY,
        'email': email
    }
    if groups:
        data['groups'] = ','.join(groups)
    url += '?' + urllib.urlencode(data)

    resp = requests.get(url)
    if not resp.status_code == 200:
        url = url.replace(settings.MOZILLIANS_API_KEY, 'xxxscrubbedxxx')
        raise BadStatusCodeError('%s: on: %s' % (resp.status_code, url))
    return json.loads(resp.content)


def is_vouched(email):
    content = _fetch_users(email)
    if content:
        for obj in content['objects']:
            if obj['email'].lower() == email.lower():
                return obj['is_vouched']
    return False


def fetch_user_name(email):
    content = _fetch_users(email)
    if content:
        for obj in content['objects']:
            if obj['email'].lower() == email.lower():
                return obj['full_name']


def in_groups(email, groups):
    if isinstance(groups, basestring):
        groups = [groups]
    content = _fetch_users(email, groups=groups)
    if content:
        for obj in content['objects']:
            if obj['email'].lower() == email.lower():
                return bool(set(groups) & set(obj['groups']))
    return False


def _fetch_groups(order_by='name', limit=20, offset=0):
    # Max limit is 500

    if not getattr(settings, 'MOZILLIANS_API_KEY', None):  # pragma no cover
        logging.warning("'MOZILLIANS_API_KEY' not set up.")
        return False

    url = settings.MOZILLIANS_API_BASE + '/api/v1/groups/'
    data = {
        'app_name': settings.MOZILLIANS_API_APPNAME,
        'app_key': settings.MOZILLIANS_API_KEY,
        'order_by': order_by,
        'limit': int(limit),
        'offset': int(offset)
    }
    url += '?' + urllib.urlencode(data)

    resp = requests.get(url)
    if not resp.status_code == 200:
        url = url.replace(settings.MOZILLIANS_API_KEY, 'xxxscrubbedxxx')
        raise BadStatusCodeError('%s: on: %s' % (resp.status_code, url))
    return json.loads(resp.content)


def get_all_groups(name_search=None):
    if name_search:
        raise NotImplementedError(
            "This is currently not yet supported. See "
            "http://mozillians.readthedocs.org/en/latest/api-groups.html"
        )

    limit = 500
    offset = 0
    all = []
    while True:
        found = _fetch_groups(limit=limit, offset=offset)
        all.extend(found['objects'])
        if len(found) < limit:
            break
        offset += limit
    return all
