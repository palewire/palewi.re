from django.template import Template, Context

from correx.models import Change
from correx.tests import ChangeTestCase
from correx.tests.models import Article, Author

class CorrexTemplateTagTests(ChangeTestCase):

    def setUp(self):
        self.createSomeChanges()

    def render(self, t, **c):
        ctx = Context(c)
        out = Template(t).render(ctx)
        return ctx, out

    def testGetChangeList(self):
        """
        Tests the tag for pulling the most recently published changes.
        """
        t = "{% load correx_tags %}{% get_latest_changes 1 as latest_changes %}"
        match = Change.objects.get(pk=6)
        ctx, out = self.render(t, c=match)
        self.assertEqual(out, "")
        self.assertEqual(list(ctx["latest_changes"]), [match])

    def testGetChangeListByUser(self):
        """
        Tests the tag for pulling the most recent changes by a particular user.
        """
        t = "{% load correx_tags %}{% get_changes_for_user Otis 1 as change_list %}"
        match = Change.objects.get(pk=6)
        ctx, out = self.render(t, c=match)
        self.assertEqual(out, "")
        self.assertEqual(list(ctx["change_list"]), [match])

    def testGetChangeListBySite(self):
        """
        Tests the tag for pulling the most recent changes for a particular site.
        """
        t = "{% load correx_tags %}{% get_changes_for_site 1881 1 as change_list %}"
        match = Change.objects.get(pk=6)
        ctx, out = self.render(t, c=match)
        self.assertEqual(out, "")
        self.assertEqual(list(ctx["change_list"]), [match])

    def testGetChangeListByApp(self):
        """
        Tests the tag for pulling the most recent changes for a particular app.
        """
        t = "{% load correx_tags %}{% get_changes_for_app tests 1 as change_list %}"
        match = Change.objects.get(pk=6)
        ctx, out = self.render(t, c=match)
        self.assertEqual(out, "")
        self.assertEqual(list(ctx["change_list"]), [match])

    def testGetChangeListByModel(self):
        """
        Tests the tag for pulling the most recent changes for a particular model.
        """
        t = "{% load correx_tags %}{% get_changes_for_model tests.Article 1 as change_list %}"
        match = Change.objects.get(pk=6)
        ctx, out = self.render(t, c=match)
        self.assertEqual(out, "")
        self.assertEqual(list(ctx["change_list"]), [match])

    def testGetChangeListByObject(self):
        """
        Tests the tag for pulling the most recent changes for a particular model.
        """
        t = "{% load correx_tags %}{% get_changes_for_object a 1 as change_list %}"
        match = Change.objects.get(pk=6)
        ctx, out = self.render(t, c=match, a=Article.objects.get(pk=1))
        self.assertEqual(out, "")
        self.assertEqual(list(ctx["change_list"]), [match])