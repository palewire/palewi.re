from fabric.api import local, hide, task


@task
def bigfiles(min_size='20000k'):
    """
    List all files in the current directory over the provided size,
    which 20MB by default.

    Example usage:

        $ fab bigfiles

    """
    cmd = """find ./ -type f -size +%s -exec ls -lh {} \; | \
awk '{ print $NF ": " $5 }'"""
    with hide('everything'):
        list_ = local(cmd % min_size)
    if list_:
        print("Files over %s" % min_size)
        print(list_)
    else:
        print("No files over %s" % min_size)
