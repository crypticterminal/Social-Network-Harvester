# coding=UTF-8

from datetime import timedelta
import resource
import time

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from snh.models.youtubemodel import *

import snhlogger
logger = snhlogger.init_logger(__name__, "youtube.log")

def run_youtube_harvester():
    harvester_list = YoutubeHarvester.objects.all()
    for harvester in harvester_list:
        logger.info(u"The harvester %s is %s" % 
                                                (unicode(harvester), 
                                                "active" if harvester.is_active else "inactive"))
        if harvester.is_active:
            run_harvester_v1(harvester)

def sleeper(retry_count):
    retry_delay = 1
    wait_delay = retry_count*retry_delay
    wait_delay = 10 if wait_delay > 10 else wait_delay
    time.sleep(wait_delay)

def get_timedelta(dm_time):
    ts = datetime.strptime(dm_time,'%Y-%m-%dT%H:%M:%S+0000')
    return (datetime.utcnow() - ts).days

def update_users(harvester):
    pass

def run_harvester_v1(harvester):
    harvester.start_new_harvest()
    try:

        start = time.time()
        update_users(harvester)
        #update_all_videos(harvester)
        logger.info(u"Results computation complete in %ss" % (time.time() - start))

    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s Mem:%s MB" % (harvester,unicode(harvester.get_stats()),unicode(getattr(usage, "ru_maxrss")/(1024.0))))

