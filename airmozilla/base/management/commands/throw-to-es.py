from pprint import pprint

import pyelasticsearch

from django.core.management.base import BaseCommand

from airmozilla.main.models import *


class Command(BaseCommand):  # pragma: no cover

    def handle(self, **options):
        es = pyelasticsearch.ElasticSearch('http://localhost:9200/')
        # es.delete_index('events')
        # es.refresh()
        for event in Event.objects.scheduled().order_by('?')[:100]:
            # should do bulk ops really but besides the point
            es.index(
                'events',
                'event',
                {
                    'title': event.title,
                    'tags': [x.name for x in event.tags.all()],
                    'channels': [x.name for x in event.channels.all()],
                },
                id=event.id,
            )
            # print event.title

        es.refresh()  # let it clear its throat
        print '-' * 100

        # get one my id
        event, = Event.objects.scheduled().order_by('?')[:1]
        try:
            doc = es.get('events', 'event', event.id)
            pprint(doc['_source'])
            assert doc['_source']['title'] == event.title
        except pyelasticsearch.exceptions.ElasticHttpNotFoundError:
            print "Not indexed yet :("

        print '-' * 100

        # search for matches by certain tags
        random_tag, = Tag.objects.all().order_by('?')[:1]
        print "Random tag:", random_tag
        hits = es.search('tag: %s' % random_tag.name, index='events')['hits']
        for doc in hits['hits']:
            event = doc['_source']
            # print "DOC", doc
            print "\t", event['title']
            print random_tag.name.lower() in [x.lower() for x in event['tags']]
        if not hits['total']:
            print "Noting found :("

        # from search by to Django ORM objects
        print '-' * 100
        hits = es.search('title: firefox', index='events')['hits']
        for doc in hits['hits']:
            event = Event.objects.get(id=doc['_id'])
            print "\t", repr(event.title), doc['_score']

        # Finding similar things using
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-mlt-query.html
        print '-' * 100
        random_event, = Event.objects.all().order_by('?')[:1]
        print "This Event:", repr(random_event.title), random_event.id
        query = {
            "query": {
                "more_like_this": {
                    "fields": ["title"],
                    "like_text": random_event.title,
                    "min_term_freq": 1,
                    "max_query_terms": 5,
                }
            }
        }
        hits = es.search(query, index='events')['hits']
        for doc in hits['hits']:
            print "\t", repr(doc['_source']['title']), doc['_id']
