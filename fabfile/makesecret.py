import random
from fabric.api import task


@task
def makesecret(
    length=50,
    allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
):
    """
    Generates secret key for use in Django settings.
    """
    key = ''.join(random.choice(allowed_chars) for i in range(length))
    print 'SECRET_KEY = "%s"' % key
