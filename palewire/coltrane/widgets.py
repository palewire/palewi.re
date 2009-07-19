# Forms
from django import forms

# Helpers
from django.utils import simplejson
from django.utils.safestring import mark_safe

# Models
from django.db.models import get_model
from tagging.models import Tag
Post = get_model('coltrane', 'post')

class AutoCompleteTagInput(forms.TextInput):
	class Media:
		css = {
			'all': ('jquery-autocomplete/jquery.autocomplete.css',)
		}
		js = (
			'jquery-autocomplete/lib/jquery.js',
			'jquery-autocomplete/lib/jquery.bgiframe.min.js',
			'jquery-autocomplete/lib/jquery.ajaxQueue.js',
			'jquery-autocomplete/jquery.autocomplete.js'
		)

	def render(self, name, value, attrs=None):
		output = super(AutoCompleteTagInput, self).render(name, value, attrs)
		page_tags = Tag.objects.usage_for_model(Post)
		tag_list = simplejson.dumps([tag.name for tag in page_tags],
									ensure_ascii=False)
		return output + mark_safe(u'''<script type="text/javascript">
			jQuery("#id_%s").autocomplete(%s, {
				width: 150,
				max: 10,
				highlight: false,
				multiple: true,
				multipleSeparator: ", ",
				scroll: true,
				scrollHeight: 300,
				matchContains: true,
				autoFill: true,
			});
			</script>''' % (name, tag_list))
