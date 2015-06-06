from .venv import _venv
from fabric.api import task


@task
def pipinstall(package=''):
    """
    Install Python requirements inside a virtualenv.
    """
    if not package:
        _venv("pip install -r requirements.txt")
    else:
        _venv("pip install %s" % package)
