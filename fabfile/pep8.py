import os
from fabric.api import local, hide, task


@task
def pep8():
    """
    Flags any violations of the Python style guide.

    Requires that you have the pep8 package installed

    Example usage:

        $ fab pep8

    Documentation:

        http://github.com/jcrocholl/pep8

    """
    print("Checking Python style")
    # Grab everything public folder inside the current directory
    dir_list = [x[0] for x in os.walk('./') if not x[0].startswith('./.')]
    # Loop through them all and run pep8
    results = []
    with hide('everything'):
        for d in dir_list:
            results.append(local("pep8 %s" % d))
    # Filter out the empty results and print the real stuff
    results = [e for e in results if e]
    for e in results:
        print(e)
