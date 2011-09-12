import random
from django import template
from datetime import datetime
from django.db.models import get_model
from coltrane.models import Post, Slogan


def do_random_slogan(parser,token):
    return RandomSloganNode()


class RandomSloganNode(template.Node):
    def render(self, context):
        try:
            random_slogan = random.choice(Slogan.objects.all())
            context['random_slogan'] = random_slogan
        except:
            context['random_slogan'] = ''
        return ''


def do_all_slogans(parser,token):
    return AllSlogansNode()


class AllSlogansNode(template.Node):
    def render(self, context):
        context['slogan_list'] = Slogan.objects.all()
        return ''


def do_latest_content(parser, token):
    bits = token.contents.split()
    if len(bits) != 5:
        raise template.TemplateSyntaxError ("'get_latest_content tag takes exactly four arguments")
    model_args = bits[1].split('.')
    if len(model_args) != 2:
        raise template.TemplateSyntaxError("First argument to 'get_latest_content' must be an 'application_name'.'model name' string")
    model = get_model(*model_args)
    if model is None:
        raise template.TemplateSyntaxError("'get_latest_content' tag got an invalid model: %s" % bits[1])
    return LatestContentNode(model, bits[2], bits[4])


class LatestContentNode(template.Node):
    def __init__(self, model, num, varname):
        self.model = model
        self.num = int(num)
        self.varname = varname

    def render(self, context):
        context[self.varname] = self.model._default_manager.all()[:self.num]
        return ''


def do_current_year(parser,token):
    return CurrentYearNode()


class CurrentYearNode(template.Node):
    def render(self, context):
        context['current_year'] = datetime.now().year
        return ''


register = template.Library()
register.tag('get_latest_content', do_latest_content)
register.tag('get_random_slogan', do_random_slogan)
register.tag('get_all_slogans', do_all_slogans)
register.tag('get_current_year', do_current_year)



