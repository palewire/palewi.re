---
title: 'Fabric recipe: delete pyc files before runserver starts'
slug: fabric-recipe-delete-pyc-files-runserver-starts
published_at: '2010-03-24T13:19:09-07:00'
---
<p>Here's a quick Fabric function that will clean out any pyc files in your Django project before firing up. It's nice to do this when you're building a site on your computer, since lingering pyc files can keep old code alive if you're not careful.</p>

<p>Fabric can also save you a keystroke or two. Heck, you could trim things down even more and name this function something like "rs."</p>

<pre lang="python">
def runserver(port=8000):
    """
    Fire up the Django test server, after cleaning out any .pyc files.

    Example usage:
    
        $ fab runserver
        $ fab runserver:port=8001
    
    """
    local("find . -name '*.pyc' -print0|xargs -0 rm", capture=False)
    local("./manage.py runserver %s" % port, capture=False)
</pre>