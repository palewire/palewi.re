from .venv import _venv
from fabric.api import env, task


@task
def pull():
    """
    Pulls the latest code using Git
    """
    _venv("git pull origin %s" % env.branch)
