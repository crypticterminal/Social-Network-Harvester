# coding=UTF-8

import sys
import os
import logging

import twitter
import time

from django.core.exceptions import ObjectDoesNotExist

from snh.models.twittermodel import *
from settings import PROJECT_PATH

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(os.path.join(PROJECT_PATH, "log/twitter.log"), mode="a+")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

def run_twitter_harvester():
    harvester_list = TwitterHarvester.objects.all()
    for harvester in harvester_list:
        logger.info(u"The harvester %s is %s" % (unicode(harvester), "active" if harvester.is_active else "inactive"))
        if harvester.is_active:
            run_harvester_v2(harvester)

def get_latest_statuses_page(harvester, user, page):
    latest_statuses_page = harvester.api_call("GetUserTimeline",
                                                {
                                                u"screen_name":unicode(user.screen_name), 
                                                u"since_id":None, 
                                                u"include_rts":True, 
                                                u"include_entities":True,
                                                u"count":200,
                                                u"page":page,
                                                })
    return latest_statuses_page

def sleeper(retry_count):
    max_retry = 5
    retry_delay = 1
    wait_delay = retry_count*retry_delay
    wait_delay = 60 if wait_delay > 60 else wait_delay
    time.sleep(wait_delay)

def get_latest_statuses(harvester, user):

    page = 0
    retry = 0
    lsp = []
    latest_statuses = []

    while True:
        try:
            logger.debug(u"%s:%s(%d):%d" % (harvester, unicode(user), user.fid if user.fid else 0, page))
            lsp = get_latest_statuses_page(harvester, user, page)
            if lsp:
                latest_statuses += lsp
            else:
                break
            page += 1
            retry = 0
        except:
            msg = u"Exception for the harvester %s for the user %s(%d) at page %d. Retry:%d" % (harvester, unicode(user), user.fid if user.fid else 0, page, retry)
            logger.exception(msg)
            retry += 1
            if retry > harvester.max_retry_on_fail:
                break
            else:
                sleeper(retry)
    return latest_statuses

def update_user(statuses, user):
        try:
            if statuses:
                user.update_from_twitter(statuses[0].user)
            else:
                user.error_triggered = True
                user.save()
                raise Exception("Cannot update user without a status!")
        except:
            msg = u"Cannot update user info for %s:(%d)" % (unicode(user), user.fid if user.fid else 0)
            logger.exception(msg)    

def update_user_statuses(statuses, user):
        for status in statuses:
            try:
                try:
                    tw_status = TWStatus.objects.get(fid__exact=status.id)
                except ObjectDoesNotExist:
                    tw_status = TWStatus()
                tw_status.update_from_twitter(status,user)
            except:
                msg = u"Cannot update status %s for %s:(%d)" % (unicode(status), unicode(user), user.fid if user.fid else 0)
                logger.exception(msg) 

def run_harvester_v2(harvester):

    harvester.start_new_harvest()
    user = harvester.get_next_user_to_harvest()
    while user:
        if not user.error_triggered:
            logger.info(u"Start: %s:%s(%d). Hits to go: %d" % (harvester, unicode(user), user.fid if user.fid else 0, harvester.remaining_hits))
            ls = get_latest_statuses(harvester, user)
            update_user(ls, user)
            update_user_statuses(ls, user)
        else:
            logger.info(u"Skipping: %s:%s(%d) because user has triggered the error flag." % (harvester, unicode(user), user.fid if user.fid else 0))
        user = harvester.get_next_user_to_harvest()
            
    harvester.end_current_harvest()
    logger.info(u"End: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
    

