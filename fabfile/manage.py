from .venv import _venv
from fabric.api import task


@task
def manage(cmd):
    """
    Run the provided Django manage.py command
    """
    _venv("python manage.py %s" % cmd)
