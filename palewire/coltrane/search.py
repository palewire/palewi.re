import solango
from coltrane.models import Post, Shout, Video, Photo, Link


class PostDocument(solango.SearchDocument):
	author = solango.fields.CharField()
	date = solango.fields.DateField()
	title = solango.fields.CharField(copy=True)
	body = solango.fields.TextField(copy=True)
	categories = solango.fields.CharField()
	tags = solango.fields.CharField()

	def transform_author(self, instance):
		return instance.author.get_full_name()

	def transform_date(self, instance):
		return instance.pub_date
		
	def transform_title(self, instance):
		return instance.title

	def transform_body(self, instance):
		from django.utils.html import strip_tags
		return strip_tags(instance.body_markup)
				
	def transform_categories(self, instance):
		return ", ".join([i.title for i in self.categories.all()])

	def transform_tags(self, instance):
		return instance.get_tags()

solango.register(Post, PostDocument)


class ShoutDocument(solango.SearchDocument):
	author = solango.fields.CharField()
	date = solango.fields.DateField()
	body = solango.fields.TextField(copy=True)

	def transform_author(self, instance):
		return instance.posted_by.get_full_name()

	def transform_date(self, instance):
		return instance.pub_date
		
	def transform_body(self, instance):
		return instance.body
				
solango.register(Shout, ShoutDocument)


class VideoDocument(solango.SearchDocument):
	author = solango.fields.CharField()
	date = solango.fields.DateField()
	body = solango.fields.TextField(copy=True)
	tags = solango.fields.CharField()

	def transform_author(self, instance):
		return instance.posted_by.get_full_name()

	def transform_date(self, instance):
		return instance.pub_date
		
	def transform_title(self, instance):
		return instance.title
		
	def transform_tags(self, instance):
		return instance.get_tags()
				
solango.register(Video, VideoDocument)


class PhotoDocument(solango.SearchDocument):
	author = solango.fields.CharField()
	date = solango.fields.DateField()
	body = solango.fields.TextField(copy=True)
	tags = solango.fields.CharField()

	def transform_author(self, instance):
		return instance.posted_by.get_full_name()

	def transform_date(self, instance):
		return instance.pub_date
		
	def transform_title(self, instance):
		return instance.title
		
	def transform_tags(self, instance):
		return instance.get_tags()
				
solango.register(Photo, PhotoDocument)


class LinkDocument(solango.SearchDocument):
	author = solango.fields.CharField()
	date = solango.fields.DateField()
	body = solango.fields.TextField(copy=True)
	tags = solango.fields.CharField()

	def transform_author(self, instance):
		return instance.posted_by.get_full_name()

	def transform_date(self, instance):
		return instance.pub_date
		
	def transform_title(self, instance):
		return instance.title
		
	def transform_tags(self, instance):
		return instance.get_tags()
				
solango.register(Link, LinkDocument)
