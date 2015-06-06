from fabric.api import env, local, task


@task
def ssh():
    """
    Log into the remote host using SSH
    """
    local("ssh ubuntu@%s -i %s" % (env.hosts[0], env.key_filename[0]))
