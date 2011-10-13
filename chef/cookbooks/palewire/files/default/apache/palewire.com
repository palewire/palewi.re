<VirtualHost *:80>
    ServerName 173.203.223.167
    ServerAlias 173.203.223.167
    WSGIScriptAlias / /apps/palewire.com/project/apache/django.wsgi
    WSGIDaemonProcess palewire user=palewire group=palewire threads=25
    WSGIProcessGroup palewire
</VirtualHost>

