from fabric.api import task, local


@task
def alertthemedia():
    """
    Ring the alarm!
    """
    local("curl -I http://databank-soundsystem.latimes.com/rollout/")
