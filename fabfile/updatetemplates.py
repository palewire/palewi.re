from fabric.api import lcd, local, task


@task
def updatetemplates(template_path='./templates'):
    """
    Download the latest template release and load it into your system.

    It will unzip to "./templates" where you run it.
    """
    url = "http://databank-cookbook.latimes.com/dist/templates/latest.zip"
    with lcd(template_path):
        local("curl -O %s" % url)
        local("unzip -o latest.zip")
        local("rm latest.zip")
