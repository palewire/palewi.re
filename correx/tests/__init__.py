from django.test import TestCase
from django.db.models.loading import get_apps, load_app

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from correx.models import Change
from correx.tests.models import Article, Author

# Add the test models to INSTALLED_APPS
# Not sure if this the best way to do it.
# I just ripped the code out of the runtests.py
# file that is packaged with 1.0
from django.conf import settings
old_installed_apps = settings.INSTALLED_APPS
model_label = 'correx.tests'
mod = load_app(model_label)
settings.INSTALLED_APPS.append(model_label)

# Shortcut
CT = ContentType.objects.get_for_model

# Helper base class for changes tests that need data.
class ChangeTestCase(TestCase):
    fixtures = ["correx_tests"]
    
    def createSomeChanges(self):
        # A change without links to objects
        change_without_link = Change.objects.create(
            description='Correction without connection', 
            change_type_id='Correction', 
            pub_date='2009-02-14',
            is_public=True
        )
        # A change with a site
        lat_data_desk = Site.objects.get(id=1881)
        change_with_site = Change.objects.create(
            description='Site-level addition', 
            change_type_id='Addition', 
            pub_date='2009-02-14', 
            site=lat_data_desk,
            is_public=True
        )
        # A change with a user
        otis = User.objects.get(username='Otis')
        change_with_user = Change.objects.create(
            description='Russ makes a site-wide addition', 
            change_type_id='Addition', 
            pub_date='2009-02-14', 
            site=lat_data_desk, 
            user=otis,
            is_public=True
        )
        # A change with an app
        author_ct = CT(Author)
        change_with_app = Change.objects.create(
            description='An app-wide update', 
            change_type_id='Update', 
            pub_date='2009-02-15', 
            site=lat_data_desk, 
            user=otis, 
            content_app=author_ct.app_label,
            is_public=True
        )
        # A change with a model
        change_with_model = Change.objects.create(
            description='An update to an author bio', 
            change_type_id='Update', 
            pub_date='2009-02-14', 
            site=lat_data_desk, 
            user=otis, 
            content_app=author_ct.app_label, 
            content_type=author_ct,
            is_public=True
        )
        # A change with an object
        article_ct = CT(Article)
        change_with_object = Change.objects.create(
            description='A correction to a story', 
            change_type_id='Correction', 
            pub_date='2009-02-16', 
            site=lat_data_desk, 
            user=otis, 
            content_app=article_ct.app_label, 
            content_type=article_ct,
            object_id = 1,
            is_public=True
        )

        return change_without_link, change_with_site, change_with_user, change_with_app, change_with_model, change_with_object

from correx.tests.unittests.model_tests import *
from correx.tests.unittests.templatetag_tests import *
from correx.tests.unittests.view_tests import *
# Resetting INSTALLED_APPS...though I'm not sure it does everything it should
settings.INSTALLED_APPS = old_installed_apps