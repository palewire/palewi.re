import os, sys
sys.path.append('/apps/palewire.com/')
sys.path.append('/apps/palewire.com/project/')
sys.path.append('/apps/palewire.com/lib/python2.7/site-packages/')
sys.path.append('/apps/palewire.com/bin/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
