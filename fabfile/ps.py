from fabric.api import run, task


@task
def ps(process='all'):
    """
    Reports a snapshot of the current processes.

    If the process kwarg provided is 'all', every current process is returned.

    Otherwise, the list will be limited to only those processes
    that match the kwarg.

    Example usage:

        $ fab prod ps:process=all
        $ fab prod ps:process=httpd
        $ fab prod ps:process=postgres

    Documentation::

        "ps":http://unixhelp.ed.ac.uk/CGI/man-cgi?ps

    """
    if process == 'all':
        run("ps aux")
    else:
        run("ps -e -O rss,pcpu | grep %s" % process)
