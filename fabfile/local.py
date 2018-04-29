from fabric.api import local, settings, task, hide


@task
def rmpyc():
    """
    Erases pyc files from current directory.

    Example usage:

        $ fab rmpyc

    """
    print("Removing .pyc files")
    with hide('everything'):
        local("find . -name '*.pyc' -print0|xargs -0 rm", capture=False)


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
