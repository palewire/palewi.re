import os
import sys

# Load Django config
current_dir = os.path.abspath(__file__)
projects_dir = os.sep.join(current_dir.split(os.sep)[:-3])
data_dir = os.path.join(projects_dir, 'rapture/archive', 'html')
os.environ['PYTHONPATH'] = projects_dir
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(projects_dir)

# Update toys
from rapture.update.models import UpdateLog
from rapture.update.archive import archive
from rapture.update.parse import parse
from rapture.update.load import load

# Helpers
import datetime
from rapture.toolbox.dprint import dprint

def run():
    # Prepare log
    now = datetime.datetime.now()
    log = UpdateLog.objects.create(start_date=now)

    # Scrape site
    soup, html_dir = archive(data_dir, now)
    
    # Update log
    log.archive_path = html_dir
    log.save()
    
    # Parse HTML
    scores_dict, comments_dict, timestamp = parse(soup)
    
    # Update db
    loaded_new_data = load(scores_dict, comments_dict, timestamp)
    
    # Finalize log
    now = datetime.datetime.now()
    log.end_date = now
    log.loaded_new_data = loaded_new_data
    log.outcome = 'complete'
    log.save()

if __name__ == '__main__':
    run()
