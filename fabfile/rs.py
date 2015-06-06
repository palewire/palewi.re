from .rmpyc import rmpyc
from fabric.api import local, settings, task


@task
def rs(port=8000):
    """
    Fire up the Django test server, after cleaning out any .pyc files.

    Example usage:

        $ fab rs
        $ fab rs:port=9000

    """
    with settings(warn_only=True):
        rmpyc()
    local("python manage.py runserver 0.0.0.0:%s" % port, capture=False)
