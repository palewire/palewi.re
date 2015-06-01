import os, sys
sys.path.append('/apps/palewi.re/')
sys.path.append('/apps/palewi.re/repo/')
sys.path.append('/apps/palewi.re/lib/python2.7/site-packages/')
sys.path.append('/apps/palewi.re/bin/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

try:
    import newrelic.agent
    newrelic.agent.initialize('/apps/palewi.re/repo/project/newrelic.ini')
    application = newrelic.agent.wsgi_application()(application)
except:
    pass
