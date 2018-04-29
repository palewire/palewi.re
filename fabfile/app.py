import os
from fabric.api import env, cd, sudo, task, local, run


@task
def collectstatic():
    """
    Roll out the latest static files
    """
    _venv("rm -rf ./static")
    _venv("python manage.py collectstatic --noinput")


@task
def clean():
    """
    Erases pyc files from our app code directory.
    """
    env.shell = "/bin/bash -c"
    with cd(env.project_dir):
        sudo("find . -name '*.pyc' -print0|xargs -0 rm", pty=True)


@task
def deploy():
    """
    Deploy the latest code and restart everything.
    """
    pull()
    with settings(warn_only=True):
        clean()
    pipinstall()
    restartapache()


@task
def manage(cmd):
    """
    Run the provided Django manage.py command
    """
    _venv("python manage.py %s" % cmd)


@task
def migrate():
    """
    Run Django's migrate command
    """
    _venv("python manage.py migrate")


@task
def pull():
    """
    Pulls the latest code using Git
    """
    _venv("git pull origin %s" % env.branch)


@task
def pipinstall(package=''):
    """
    Install Python requirements inside a virtualenv.
    """
    if not package:
        _venv("pip install -r requirements.txt")
    else:
        _venv("pip install %s" % package)


@task
def pushsettings():
    """
    Push private files that aren't store in Git repository to remote hosts.
    """
    for file_name in ["settings_prod.py", "newrelic.ini"]:
        put(
            os.path.join(env.local_project_dir, 'project', file_name),
            os.path.join('/tmp', file_name),
        )
        sudo("mv %s %s" % (
            os.path.join('/tmp', file_name),
            os.path.join(env.project_dir, 'project', file_name),
        ))


@task
def restartvarnish():
    """
    Restart the Varnish cache service
    """
    sudo("service varnish restart", pty=True)


@task
def restartapache():
    """
    Restarts apache on both app servers.
    """
    sudo("/etc/init.d/apache2 reload", pty=True)


@task
def ssh():
    """
    Log into the remote host using SSH
    """
    local("ssh %s@%s -i %s" % (env.app_user, env.hosts[0], env.key_filename[0]))


def _venv(cmd):
    """
    Runs the provided command in a remote virturalenv
    """
    with cd(env.project_dir):
        sudo(
            "%s && %s" % (env.activate, cmd),
            user=env.app_user
        )
