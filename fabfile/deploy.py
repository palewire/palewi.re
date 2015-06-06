from fabric.api import settings, task
from .pull import pull
from .clean import clean
from .pipinstall import pipinstall
from .restartapache import restartapache


@task
def deploy():
    """
    Deploy the latest code and restart everything.
    """
    pull()
    with settings(warn_only=True):
        clean()
    pipinstall()
    restartapache()
