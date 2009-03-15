from django import forms
from django.db.models import get_model
from tagging.forms import TagField
from coltrane.widgets import AutoCompleteTagInput

class PostAdminModelForm(forms.ModelForm):
    tags = TagField(widget=AutoCompleteTagInput(), required=False)

    class Meta:
        model = get_model('coltrane', 'post')
