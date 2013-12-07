# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Ticker'
        db.create_table(u'coltrane_ticker', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'coltrane', ['Ticker'])

        # Adding model 'Slogan'
        db.create_table(u'coltrane_slogan', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal(u'coltrane', ['Slogan'])

        # Adding model 'Category'
        db.create_table(u'coltrane_category', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('post_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'coltrane', ['Category'])

        # Adding model 'Post'
        db.create_table(u'coltrane_post', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('wordpress_id', self.gf('django.db.models.fields.IntegerField')(unique=True, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=300)),
            ('body_markup', self.gf('django.db.models.fields.TextField')()),
            ('body_html', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('enable_comments', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('tags', self.gf('tagging.fields.TagField')()),
        ))
        db.send_create_signal(u'coltrane', ['Post'])

        # Adding M2M table for field categories on 'Post'
        m2m_table_name = db.shorten_name(u'coltrane_post_categories')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm[u'coltrane.post'], null=False)),
            ('category', models.ForeignKey(orm[u'coltrane.category'], null=False))
        ))
        db.create_unique(m2m_table_name, ['post_id', 'category_id'])

        # Adding model 'Beer'
        db.create_table(u'coltrane_beer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tags', self.gf('tagging.fields.TagField')(max_length=1000)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250, null=True, blank=True)),
            ('brewery', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal(u'coltrane', ['Beer'])

        # Adding model 'Book'
        db.create_table(u'coltrane_book', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tags', self.gf('tagging.fields.TagField')(max_length=1000)),
            ('isbn', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('authors', self.gf('django.db.models.fields.CharField')(max_length=250, null=True, blank=True)),
        ))
        db.send_create_signal(u'coltrane', ['Book'])

        # Adding model 'Link'
        db.create_table(u'coltrane_link', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tags', self.gf('tagging.fields.TagField')(max_length=1000)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'coltrane', ['Link'])

        # Adding model 'Commit'
        db.create_table(u'coltrane_commit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tags', self.gf('tagging.fields.TagField')(max_length=1000)),
            ('repository', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('branch', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('message', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'coltrane', ['Commit'])

        # Adding model 'Location'
        db.create_table(u'coltrane_location', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tags', self.gf('tagging.fields.TagField')(max_length=1000)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(null=True)),
        ))
        db.send_create_signal(u'coltrane', ['Location'])

        # Adding model 'Movie'
        db.create_table(u'coltrane_movie', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tags', self.gf('tagging.fields.TagField')(max_length=1000)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250, null=True, blank=True)),
            ('rating', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'coltrane', ['Movie'])

        # Adding model 'Photo'
        db.create_table(u'coltrane_photo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tags', self.gf('tagging.fields.TagField')(max_length=1000)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=250, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'coltrane', ['Photo'])

        # Adding model 'Shout'
        db.create_table(u'coltrane_shout', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tags', self.gf('tagging.fields.TagField')(max_length=1000)),
            ('message', self.gf('django.db.models.fields.TextField')(max_length=140)),
        ))
        db.send_create_signal(u'coltrane', ['Shout'])

        # Adding model 'Track'
        db.create_table(u'coltrane_track', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1000)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('tags', self.gf('tagging.fields.TagField')(max_length=1000)),
            ('artist_name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('track_name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('track_mbid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('artist_mbid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'coltrane', ['Track'])

        # Adding model 'TopDomain'
        db.create_table(u'coltrane_topdomain', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('count', self.gf('django.db.models.fields.IntegerField')()),
            ('stratum', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'coltrane', ['TopDomain'])

        # Adding model 'TopTag'
        db.create_table(u'coltrane_toptag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tagging.Tag'], unique=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('count', self.gf('django.db.models.fields.IntegerField')()),
            ('stratum', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'coltrane', ['TopTag'])


    def backwards(self, orm):
        # Deleting model 'Ticker'
        db.delete_table(u'coltrane_ticker')

        # Deleting model 'Slogan'
        db.delete_table(u'coltrane_slogan')

        # Deleting model 'Category'
        db.delete_table(u'coltrane_category')

        # Deleting model 'Post'
        db.delete_table(u'coltrane_post')

        # Removing M2M table for field categories on 'Post'
        db.delete_table(db.shorten_name(u'coltrane_post_categories'))

        # Deleting model 'Beer'
        db.delete_table(u'coltrane_beer')

        # Deleting model 'Book'
        db.delete_table(u'coltrane_book')

        # Deleting model 'Link'
        db.delete_table(u'coltrane_link')

        # Deleting model 'Commit'
        db.delete_table(u'coltrane_commit')

        # Deleting model 'Location'
        db.delete_table(u'coltrane_location')

        # Deleting model 'Movie'
        db.delete_table(u'coltrane_movie')

        # Deleting model 'Photo'
        db.delete_table(u'coltrane_photo')

        # Deleting model 'Shout'
        db.delete_table(u'coltrane_shout')

        # Deleting model 'Track'
        db.delete_table(u'coltrane_track')

        # Deleting model 'TopDomain'
        db.delete_table(u'coltrane_topdomain')

        # Deleting model 'TopTag'
        db.delete_table(u'coltrane_toptag')


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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'coltrane.beer': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Beer'},
            'brewery': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'tags': ('tagging.fields.TagField', [], {'max_length': '1000'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        u'coltrane.book': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Book'},
            'authors': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isbn': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'tags': ('tagging.fields.TagField', [], {'max_length': '1000'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        u'coltrane.category': {
            'Meta': {'ordering': "['title']", 'object_name': 'Category'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'coltrane.commit': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Commit'},
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'repository': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tags': ('tagging.fields.TagField', [], {'max_length': '1000'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        u'coltrane.link': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Link'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'tags': ('tagging.fields.TagField', [], {'max_length': '1000'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        u'coltrane.location': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Location'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'tags': ('tagging.fields.TagField', [], {'max_length': '1000'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        u'coltrane.movie': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Movie'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'rating': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'tags': ('tagging.fields.TagField', [], {'max_length': '1000'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        u'coltrane.photo': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Photo'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'tags': ('tagging.fields.TagField', [], {'max_length': '1000'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        u'coltrane.post': {
            'Meta': {'ordering': "['-pub_date']", 'object_name': 'Post'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'body_html': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'body_markup': ('django.db.models.fields.TextField', [], {}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['coltrane.Category']", 'symmetrical': 'False'}),
            'enable_comments': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '300'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'tags': ('tagging.fields.TagField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'wordpress_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'coltrane.shout': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Shout'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'max_length': '140'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'tags': ('tagging.fields.TagField', [], {'max_length': '1000'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        u'coltrane.slogan': {
            'Meta': {'ordering': "['title']", 'object_name': 'Slogan'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'coltrane.ticker': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Ticker'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'coltrane.topdomain': {
            'Meta': {'ordering': "('-count', 'name')", 'object_name': 'TopDomain'},
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'stratum': ('django.db.models.fields.IntegerField', [], {})
        },
        u'coltrane.toptag': {
            'Meta': {'ordering': "('-count', 'name')", 'object_name': 'TopTag'},
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'stratum': ('django.db.models.fields.IntegerField', [], {}),
            'tag': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tagging.Tag']", 'unique': 'True'})
        },
        u'coltrane.track': {
            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'Track'},
            'artist_mbid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'artist_name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'tags': ('tagging.fields.TagField', [], {'max_length': '1000'}),
            'track_mbid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'track_name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1000'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'tagging.tag': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['coltrane']