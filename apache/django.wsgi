import os, sys
sys.path.append('/apps/palewi.re/')
sys.path.append('/apps/palewi.re/repo/')
sys.path.append('/apps/palewi.re/lib/python2.7/site-packages/')
sys.path.append('/apps/palewi.re/bin/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
