from fabric.api import local, hide, task


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
