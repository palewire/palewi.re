# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models

class WpAkTwitter(models.Model):
    id = models.IntegerField(primary_key=True)
    tw_id = models.CharField(max_length=765)
    tw_text = models.CharField(max_length=765)
    tw_created_at = models.DateTimeField()
    modified = models.DateTimeField()
    class Meta:
        db_table = u'wp_ak_twitter'

class WpCformsdata(models.Model):
    f_id = models.IntegerField(primary_key=True)
    sub_id = models.IntegerField()
    field_name = models.CharField(max_length=300)
    field_val = models.TextField(blank=True)
    class Meta:
        db_table = u'wp_cformsdata'

class WpCformssubmissions(models.Model):
    id = models.IntegerField(primary_key=True)
    form_id = models.CharField(max_length=9, blank=True)
    sub_date = models.DateTimeField()
    email = models.CharField(max_length=120, blank=True)
    ip = models.CharField(max_length=45, blank=True)
    class Meta:
        db_table = u'wp_cformssubmissions'

class WpComments(models.Model):
    comment_id = models.IntegerField(primary_key=True, db_column='comment_ID') # Field name made lowercase.
    comment_post_id = models.IntegerField(db_column='comment_post_ID') # Field name made lowercase.
    comment_author = models.TextField()
    comment_author_email = models.CharField(max_length=300)
    comment_author_url = models.CharField(max_length=600)
    comment_author_ip = models.CharField(max_length=300, db_column='comment_author_IP') # Field name made lowercase.
    comment_date = models.DateTimeField()
    comment_date_gmt = models.DateTimeField()
    comment_content = models.TextField()
    comment_karma = models.IntegerField()
    comment_approved = models.CharField(max_length=60)
    comment_agent = models.CharField(max_length=765)
    comment_type = models.CharField(max_length=60)
    comment_parent = models.IntegerField()
    user_id = models.IntegerField()
    comment_enclosure = models.TextField(blank=True)
    class Meta:
        db_table = u'wp_comments'

class WpEzscrobblerCache(models.Model):
    id = models.IntegerField(primary_key=True)
    cache_type = models.CharField(max_length=765, blank=True)
    xml_data = models.TextField(blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = u'wp_ezscrobbler_cache'

class WpEzscrobblerSettings(models.Model):
    id = models.IntegerField(primary_key=True)
    last_fm_user = models.CharField(max_length=765, blank=True)
    link_format = models.CharField(max_length=765, blank=True)
    date_format = models.CharField(max_length=765, blank=True)
    base_tag = models.CharField(max_length=765, blank=True)
    num_songs = models.IntegerField(null=True, blank=True)
    cache_age = models.IntegerField(null=True, blank=True)
    progress_image = models.CharField(max_length=765, blank=True)
    remote_port = models.CharField(max_length=24, blank=True)
    remote_host = models.CharField(max_length=765, blank=True)
    remote_path = models.CharField(max_length=765, blank=True)
    remote_timeout = models.IntegerField(null=True, blank=True)
    link_profile = models.IntegerField(null=True, blank=True)
    link_weekly = models.IntegerField(null=True, blank=True)
    link_recent = models.IntegerField(null=True, blank=True)
    link_top = models.IntegerField(null=True, blank=True)
    link_albums = models.IntegerField(null=True, blank=True)
    default_link = models.CharField(max_length=48, blank=True)
    open_new_window = models.IntegerField(null=True, blank=True)
    time_offset = models.CharField(max_length=765, blank=True)
    scrobbler_version = models.CharField(max_length=24, blank=True)
    use_db_cache = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'wp_ezscrobbler_settings'

class WpFsData(models.Model):
    time_install = models.IntegerField()
    max_visits = models.IntegerField()
    max_visits_time = models.IntegerField()
    max_online = models.IntegerField()
    max_online_time = models.IntegerField()
    class Meta:
        db_table = u'wp_fs_data'

class WpFsVisits(models.Model):
    visit_id = models.IntegerField(primary_key=True)
    ip = models.CharField(max_length=60)
    referer = models.CharField(max_length=765)
    platform = models.CharField(max_length=150)
    browser = models.CharField(max_length=150)
    version = models.CharField(max_length=45)
    search_terms = models.CharField(max_length=765)
    url = models.CharField(max_length=765)
    time_begin = models.IntegerField()
    time_last = models.IntegerField()
    class Meta:
        db_table = u'wp_fs_visits'

class WpGeopress(models.Model):
    geopress_id = models.IntegerField(unique=True)
    name = models.TextField()
    loc = models.TextField(blank=True)
    warn = models.TextField(blank=True)
    mapurl = models.TextField(blank=True)
    coord = models.TextField()
    geom = models.CharField(max_length=48)
    relationshiptag = models.TextField(blank=True)
    featuretypetag = models.TextField(blank=True)
    elev = models.FloatField(null=True, blank=True)
    floor = models.FloatField(null=True, blank=True)
    radius = models.FloatField(null=True, blank=True)
    visible = models.IntegerField(null=True, blank=True)
    map_format = models.TextField(blank=True)
    map_zoom = models.IntegerField(null=True, blank=True)
    map_type = models.TextField(blank=True)
    class Meta:
        db_table = u'wp_geopress'

class WpLinks(models.Model):
    link_id = models.IntegerField(primary_key=True)
    link_url = models.CharField(max_length=765)
    link_name = models.CharField(max_length=765)
    link_image = models.CharField(max_length=765)
    link_target = models.CharField(max_length=75)
    link_category = models.IntegerField()
    link_description = models.CharField(max_length=765)
    link_visible = models.CharField(max_length=60)
    link_owner = models.IntegerField()
    link_rating = models.IntegerField()
    link_updated = models.DateTimeField()
    link_rel = models.CharField(max_length=765)
    link_notes = models.TextField()
    link_rss = models.CharField(max_length=765)
    class Meta:
        db_table = u'wp_links'

class WpOptions(models.Model):
    option_id = models.IntegerField(primary_key=True)
    blog_id = models.IntegerField(primary_key=True)
    option_name = models.CharField(max_length=192)
    option_value = models.TextField()
    autoload = models.CharField(max_length=60)
    class Meta:
        db_table = u'wp_options'

class WpPodpressStatcounts(models.Model):
    postid = models.IntegerField(db_column='postID') # Field name made lowercase.
    media = models.CharField(max_length=765, primary_key=True)
    total = models.IntegerField(null=True, blank=True)
    feed = models.IntegerField(null=True, blank=True)
    web = models.IntegerField(null=True, blank=True)
    play = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'wp_podpress_statcounts'

class WpPodpressStats(models.Model):
    id = models.IntegerField(unique=True, primary_key=True)
    postid = models.IntegerField(db_column='postID') # Field name made lowercase.
    media = models.CharField(max_length=765)
    method = models.CharField(max_length=150)
    remote_ip = models.CharField(max_length=45)
    country = models.CharField(max_length=150)
    language = models.CharField(max_length=15)
    domain = models.CharField(max_length=765)
    referer = models.CharField(max_length=765)
    resource = models.CharField(max_length=765)
    user_agent = models.CharField(max_length=765)
    platform = models.CharField(max_length=150)
    browser = models.CharField(max_length=150)
    version = models.CharField(max_length=45)
    dt = models.IntegerField()
    class Meta:
        db_table = u'wp_podpress_stats'

class WpPollsa(models.Model):
    polla_aid = models.IntegerField(primary_key=True)
    polla_qid = models.IntegerField()
    polla_answers = models.CharField(max_length=600)
    polla_votes = models.IntegerField()
    class Meta:
        db_table = u'wp_pollsa'

class WpPollsip(models.Model):
    pollip_id = models.IntegerField(primary_key=True)
    pollip_qid = models.CharField(max_length=30)
    pollip_aid = models.CharField(max_length=30)
    pollip_ip = models.CharField(max_length=300)
    pollip_host = models.CharField(max_length=600)
    pollip_timestamp = models.CharField(max_length=60)
    pollip_user = models.TextField()
    pollip_userid = models.IntegerField()
    class Meta:
        db_table = u'wp_pollsip'

class WpPollsq(models.Model):
    pollq_id = models.IntegerField(primary_key=True)
    pollq_question = models.CharField(max_length=600)
    pollq_timestamp = models.CharField(max_length=60)
    pollq_totalvotes = models.IntegerField()
    pollq_active = models.IntegerField()
    pollq_expiry = models.CharField(max_length=60)
    pollq_multiple = models.IntegerField()
    pollq_totalvoters = models.IntegerField()
    class Meta:
        db_table = u'wp_pollsq'

class WpPostmeta(models.Model):
    meta_id = models.IntegerField(primary_key=True)
    post_id = models.IntegerField()
    meta_key = models.CharField(max_length=765, blank=True)
    meta_value = models.TextField(blank=True)
    class Meta:
        db_table = u'wp_postmeta'

class WpPosts(models.Model):
    id = models.IntegerField(db_column='ID', primary_key=True) # Field name made lowercase.
    post_author = models.IntegerField()
    post_date = models.DateTimeField()
    post_date_gmt = models.DateTimeField()
    post_content = models.TextField()
    post_title = models.TextField()
    post_category = models.IntegerField()
    post_excerpt = models.TextField()
    post_status = models.CharField(max_length=60)
    comment_status = models.CharField(max_length=60)
    ping_status = models.CharField(max_length=60)
    post_password = models.CharField(max_length=60)
    post_name = models.CharField(max_length=600)
    to_ping = models.TextField()
    pinged = models.TextField()
    post_modified = models.DateTimeField()
    post_modified_gmt = models.DateTimeField()
    post_content_filtered = models.TextField()
    post_parent = models.IntegerField()
    guid = models.CharField(max_length=765)
    menu_order = models.IntegerField()
    post_type = models.CharField(max_length=60)
    post_mime_type = models.CharField(max_length=300)
    comment_count = models.IntegerField()
    class Meta:
        db_table = u'wp_posts'

class WpRatings(models.Model):
    rating_id = models.IntegerField(primary_key=True)
    rating_postid = models.IntegerField()
    rating_posttitle = models.TextField()
    rating_rating = models.IntegerField()
    rating_timestamp = models.CharField(max_length=45)
    rating_ip = models.CharField(max_length=120)
    rating_host = models.CharField(max_length=600)
    rating_username = models.CharField(max_length=150)
    rating_userid = models.IntegerField()
    class Meta:
        db_table = u'wp_ratings'

class WpSimilarPosts(models.Model):
    pid = models.IntegerField(db_column='pID') # Field name made lowercase.
    content = models.TextField()
    title = models.TextField()
    tags = models.TextField()
    class Meta:
        db_table = u'wp_similar_posts'

class WpTermRelationships(models.Model):
    object_id = models.IntegerField(primary_key=True)
    term_taxonomy_id = models.IntegerField()
    term_order = models.IntegerField()
    class Meta:
        db_table = u'wp_term_relationships'

class WpTermTaxonomy(models.Model):
    term_taxonomy_id = models.IntegerField(primary_key=True)
    term_id = models.IntegerField(unique=True)
    taxonomy = models.CharField(unique=True, max_length=96)
    description = models.TextField()
    parent = models.IntegerField()
    count = models.IntegerField()
    class Meta:
        db_table = u'wp_term_taxonomy'

class WpTerms(models.Model):
    term_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=165)
    slug = models.CharField(unique=True, max_length=600)
    term_group = models.IntegerField()
    class Meta:
        db_table = u'wp_terms'

class WpUsermeta(models.Model):
    umeta_id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    meta_key = models.CharField(max_length=765, blank=True)
    meta_value = models.TextField(blank=True)
    class Meta:
        db_table = u'wp_usermeta'

class WpUsers(models.Model):
    id = models.IntegerField(primary_key=True, db_column='ID') # Field name made lowercase.
    user_login = models.CharField(max_length=180)
    user_pass = models.CharField(max_length=192)
    user_nicename = models.CharField(max_length=150)
    user_email = models.CharField(max_length=300)
    user_url = models.CharField(max_length=300)
    user_registered = models.DateTimeField()
    user_activation_key = models.CharField(max_length=180)
    user_status = models.IntegerField()
    display_name = models.CharField(max_length=750)
    class Meta:
        db_table = u'wp_users'

