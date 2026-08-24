---
title: New, improved, even more conspicuous consumption
slug: new-improved-even-more-conspicuous-consumption
published_at: '2009-07-29T09:42:08-07:00'
---
<p>This morning I added Readernaut support, with <a href="http://readernaut.com/palewire/">the latest books I post</a> syncing and republishing here.</p>

<p>The system works almost identically to the other services, with a slightly different database structure. The Book model in my Django system inherits from an abstract model that is common to all of the third-party data like Flickr and Twitter. That helps simplify the code and ensure a baseline consistency so that I can reliably expect each data set to slot into the <a href="/ticker/page/1/">sitewide ticker</a>.</p>

<p>Here's a taste. You can find <a href="http://github.com/palewire/palewire.com/tree/master">the whole codebase on github.</a></p>

<pre lang="python">
class ThirdPartyBaseModel(models.Model):
    """
    A base model for the data we'll be pulling from third-party sites.
    """
    url = models.URLField(max_length=1000)
    pub_date = models.DateTimeField(default=datetime.datetime.now, verbose_name=_('publication date'))
    tags = TagField(help_text=_('Separate tags with spaces.'), max_length=1000)
    objects = models.Manager()
    sync = SyncManager()
	
    class Meta:
        ordering = ('-pub_date',)
        abstract = True

    def get_rendered_html(self):
        template_name = 'coltrane/ticker_item_%s.html' % (self.__class__.__name__.lower())
        return render_to_string(template_name, { 'object': self })

    def get_absolute_icon(self):
        name = u'%ss' % self.__class__.__name__.lower()
        return u'/media/icons/%s.gif' % name

    def get_tag_list(self, last_word='and'):
        return get_text_list(self.tags.split(' '), last_word)
    tag_list = property(get_tag_list)


class Book(ThirdPartyBaseModel):
    """
    Books I've read.
    """
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=250)
    authors = models.CharField(max_length=250, blank=True, null=True)

    def __unicode__(self):
        if self.authors:
            return "%s by %s" % (self.title, self.authors)
        else:
            return self.title


class Shout(ThirdPartyBaseModel):
    """
    Shorter things I blast out.
    """
    message = models.TextField(max_length=140)

    def __unicode__(self):
        return self.message
		
    def get_short_message(self, words=8):
        """
        Trims message to the specified number of words.
		
        Good for use in the admin.
        """
        return truncate_words(strip_tags(self.message), words)
    short_message = property(get_short_message)

</pre>