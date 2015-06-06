import os
from fabric.api import put, sudo, task, env, run


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
