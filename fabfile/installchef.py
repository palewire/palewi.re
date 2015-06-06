from fabric.api import sudo, task


@task
def installchef():
    """
    Install all the dependencies to run a Chef cookbook
    """
    # Install dependencies
    sudo('apt-get update', pty=True)
    sudo('apt-get install -y git-core', pty=True)
    # Install Chef
    sudo('curl -L https://www.opscode.com/chef/install.sh | bash', pty=True)
    sudo('ln -s /opt/chef/bin/chef-solo /usr/local/bin/chef-solo')
