# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field region on 'Location'
        db.create_table(u'main_location_region', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('location', models.ForeignKey(orm[u'main.location'], null=False)),
            ('region', models.ForeignKey(orm[u'main.region'], null=False))
        ))
        db.create_unique(u'main_location_region', ['location_id', 'region_id'])


    def backwards(self, orm):
        # Removing M2M table for field region on 'Location'
        db.delete_table('main_location_region')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'main.approval': {
            'Meta': {'object_name': 'Approval'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Event']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'processed_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        u'main.channel': {
            'Meta': {'ordering': "['name']", 'object_name': 'Channel'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'exclude_from_trending': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'image_is_banner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Channel']", 'null': 'True'}),
            'reverse_order': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'main.curatedgroup': {
            'Meta': {'object_name': 'CuratedGroup'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'})
        },
        u'main.event': {
            'Meta': {'object_name': 'Event'},
            'additional_links': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'archive_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'call_info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'channels': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main.Channel']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'creator'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'duration': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Location']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modified_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'modified_user'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'mozillian': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'participants': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main.Participant']", 'symmetrical': 'False'}),
            'picture': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_picture'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['main.Picture']"}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'placeholder_img': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'popcorn_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'privacy': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '40', 'db_index': 'True'}),
            'recruitmentmessage': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.RecruitmentMessage']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'remote_presenters': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'short_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '215', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'initiated'", 'max_length': '20', 'db_index': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Template']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'template_environment': ('airmozilla.main.fields.EnvironmentField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'transcript': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'upload': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'event_upload'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['uploads.Upload']"})
        },
        u'main.eventassignment': {
            'Meta': {'object_name': 'EventAssignment'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Event']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main.Location']", 'symmetrical': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'main.eventhitstats': {
            'Meta': {'object_name': 'EventHitStats'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Event']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            'shortcode': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'total_hits': ('django.db.models.fields.IntegerField', [], {})
        },
        u'main.eventoldslug': {
            'Meta': {'object_name': 'EventOldSlug'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '215'})
        },
        u'main.eventrevision': {
            'Meta': {'object_name': 'EventRevision'},
            'additional_links': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'call_info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'channels': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main.Channel']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'picture': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Picture']", 'null': 'True', 'blank': 'True'}),
            'placeholder_img': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'recruitmentmessage': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.RecruitmentMessage']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'short_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'})
        },
        u'main.eventtweet': {
            'Meta': {'object_name': 'EventTweet'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'error': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_placeholder': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            'sent_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'tweet_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'main.location': {
            'Meta': {'ordering': "['name']", 'object_name': 'Location'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'region': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['main.Region']", 'null': 'True', 'blank': 'True'}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'main.locationdefaultenvironment': {
            'Meta': {'unique_together': "(('location', 'privacy', 'template'),)", 'object_name': 'LocationDefaultEnvironment'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Location']"}),
            'privacy': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '40'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Template']"}),
            'template_environment': ('airmozilla.main.fields.EnvironmentField', [], {})
        },
        u'main.participant': {
            'Meta': {'object_name': 'Participant'},
            'blog_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'clear_token': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'cleared': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '15', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'participant_creator'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'department': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'irc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'photo': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '65', 'blank': 'True'}),
            'team': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'topic_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        u'main.picture': {
            'Meta': {'object_name': 'Picture'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'picture_event'", 'null': 'True', 'to': u"orm['main.Event']"}),
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'modified_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'size': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'main.recruitmentmessage': {
            'Meta': {'ordering': "['text']", 'object_name': 'RecruitmentMessage'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'modified_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'main.region': {
            'Meta': {'ordering': "['name']", 'object_name': 'Region'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        u'main.suggestedevent': {
            'Meta': {'object_name': 'SuggestedEvent'},
            'accepted': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Event']", 'null': 'True', 'blank': 'True'}),
            'additional_links': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'call_info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'channels': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main.Channel']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'first_submitted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Location']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'participants': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main.Participant']", 'symmetrical': 'False'}),
            'picture': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Picture']", 'null': 'True', 'blank': 'True'}),
            'placeholder_img': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'popcorn_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'privacy': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '40'}),
            'remote_presenters': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'review_comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'short_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '215', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '40'}),
            'submitted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'upcoming': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'upload': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'upload'", 'null': 'True', 'to': u"orm['uploads.Upload']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'main.suggestedeventcomment': {
            'Meta': {'object_name': 'SuggestedEventComment'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'suggested_event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.SuggestedEvent']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        u'main.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'main.template': {
            'Meta': {'ordering': "['name']", 'object_name': 'Template'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'default_archive_template': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'default_popcorn_template': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'main.urlmatch': {
            'Meta': {'object_name': 'URLMatch'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'string': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'use_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'main.urltransform': {
            'Meta': {'object_name': 'URLTransform'},
            'find': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.URLMatch']"}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'replace_with': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'main.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'contributor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'main.vidlysubmission': {
            'Meta': {'object_name': 'VidlySubmission'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Event']"}),
            'hd': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submission_error': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'submission_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 21, 0, 0)'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'token_protection': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'uploads.upload': {
            'Meta': {'object_name': 'Upload'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'event'", 'null': 'True', 'to': u"orm['main.Event']"}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mime_type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'size': ('django.db.models.fields.BigIntegerField', [], {}),
            'suggested_event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggested_event'", 'null': 'True', 'to': u"orm['main.SuggestedEvent']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '400'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['main']