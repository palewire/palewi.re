from .rmpyc import rmpyc
from fabric.api import local, task


@task
def sh():
    """
    Fire up the Django shell, after cleaning out any .pyc files.

    Example usage:

        $ fab sh

    """
    rmpyc()
    local("python manage.py shell", capture=False)
