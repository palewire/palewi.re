from .venv import _venv
from fabric.api import task


@task
def collectstatic():
    """
    Roll out the latest static files
    """
    _venv("rm -rf ./static")
    _venv("python manage.py collectstatic --noinput")
