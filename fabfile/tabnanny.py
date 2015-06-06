from fabric.api import hide, local, task


@task
def tabnanny():
    """
    Checks whether any of your files have improper tabs

    Example usage:

        $ fab tabnanny

    """
    print("Running tabnanny")
    with hide('everything'):
        local("python -m tabnanny ./")
