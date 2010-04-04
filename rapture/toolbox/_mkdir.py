import os

def _mkdir(newdir):
    """
    A more friendly mkdir() than Python's standard os.mkdir(). 

    Features: 
    * Already exists, silently complete
    * Regular file in the way, raise an exception
    * Parent directory(ies) does not exist, make them as well

    Limitations: it doesn't take the optional 'mode' argument yet.
    
    Source: http://code.activestate.com/recipes/82465/
    
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        if tail:
            os.mkdir(newdir)
