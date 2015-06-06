from fabric.api import sudo, task


@task
def restartapache():
    """
    Restarts apache on both app servers.
    """
    sudo("/etc/init.d/apache2 reload", pty=True)
