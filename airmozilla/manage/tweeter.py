import datetime
import time
import os
import logging

#from twython import Twython
import twython

from django.utils.timezone import utc
from django.conf import settings

from airmozilla.main.helpers import thumbnail


def send_tweet(event_tweet, save=True):
    if event_tweet.include_placeholder:
        thumb = thumbnail(
            event_tweet.event.placeholder_img,
            '300x300'
        )
        file_path = thumb.storage.path(thumb.name)
    else:
        file_path = None

    text = event_tweet.text
    # due to a bug in twython
    # https://github.com/ryanmcgrath/twython/issues/154
    # we're not able to send non-ascii characters properly
    # Hopefully this can go away sometime soon.
    text = text.encode('utf-8')
    try:
        tweet_id = _send(text, file_path=file_path)
        event_tweet.tweet_id = tweet_id
    except Exception, msg:
        logging.error("Failed to send tweet", exc_info=True)
        event_tweet.error = str(msg)
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    event_tweet.sent_date = now
    save and event_tweet.save()


def _send(text, file_path=None):
    if file_path:
        assert os.path.isfile(file_path), file_path

    t0 = time.time()
    twitter = twython.Twython(
        twitter_token=settings.TWITTER_CONSUMER_KEY,
        twitter_secret=settings.TWITTER_CONSUMER_SECRET,
        oauth_token=settings.TWITTER_ACCESS_TOKEN,
        oauth_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
    )
    t1 = time.time()
    logging.info("Took %s seconds to connect to Twitter" % (t1 - t0))

    t0 = time.time()
    if file_path:
        new_entry = twitter.updateStatusWithMedia(
            file_path,
            status=text
        )
    else:
        new_entry = twitter.updateStatus(
            status=text
        )
    t1 = time.time()
    logging.info("Took %s seconds to tweet with media" % (t1 - t0))

    return new_entry['id']
