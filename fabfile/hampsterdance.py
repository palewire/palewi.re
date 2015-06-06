from fabric.api import task, local


@task
def hampsterdance():
    """
    The soundtrack of the Internet that once was.
    """
    local("curl -I http://databank-soundsystem.latimes.com/hampster-dance/")
