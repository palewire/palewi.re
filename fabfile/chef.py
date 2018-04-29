import boto
import time
import boto.ec2
from fabric.api import env, task, sudo
from fabric.contrib.project import rsync_project
from .app import pushsettings, manage


@task
def bootstrap():
    installchef()
    cook()
    pushsettings()
    manage("loaddb")


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


@task
def cook():
    """
    Update Chef cookbook and execute it.
    """
    sudo('mkdir -p /etc/chef')
    sudo('chown ubuntu -R /etc/chef')
    rsync_project("/etc/chef/", "./chef/")
    sudo('cd /etc/chef && %s' % env.chef, pty=True)


@task
def createserver(
        region='us-west-2',
        ami='ami-bd471c8d',
        key_name='palewire',
        instance_type='t2.small',
    ):
    """
    Spin up a new server on Amazon EC2.

    Returns the id and public address.

    By default, we use Ubuntu 12.04 LTS
    """
    print("Warming up...")
    conn = boto.ec2.connect_to_region(
        region,
        aws_access_key_id=env.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
    )
    print("Reserving an instance...")
    reservation = conn.run_instances(
        ami,
        key_name=key_name,
        instance_type=instance_type,
    )
    instance = reservation.instances[0]
    print('Waiting for instance to start...')
    # Check up on its status every so often
    status = instance.update()
    while status == 'pending':
        time.sleep(10)
        status = instance.update()
    if status == 'running':
        print('New instance %s' % instance.id)
        print('Accessible at %s' % instance.public_dns_name)
    else:
        print('Instance status: ' + status)
    return (instance.id, instance.public_dns_name)
