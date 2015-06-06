from fabric.api import env, task
from .installchef import installchef
from .cook import cook
from .pushsettings import pushsettings
from .manage import manage


@task
def bootstrap():
    installchef()
    cook()
    pushsettings()
    manage("loaddb")