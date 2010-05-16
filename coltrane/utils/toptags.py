"""
Can be scheduled as a cron to update TopTag model
"""
import os
import sys

# Set the directories and django config so it can be run from cron.
current_dir = os.path.abspath(__file__)
projects_dir = os.sep.join(current_dir.split(os.sep)[:-3])
os.environ['PYTHONPATH'] = projects_dir
sys.path.append(projects_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

if __name__ == '__main__':
    from coltrane.models import TopTag
    TopTag.update.ranking()
