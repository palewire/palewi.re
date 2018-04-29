from venv import _venv
from fabric.api import task


@task
def migrate():
    """
    Run Django's migrate command
    """
    _venv("python manage.py migrate")
