from fabric.api import sudo, task


@task
def restartvarnish():
    """
    Restart the Varnish cache service
    """
    sudo("service varnish restart", pty=True)
