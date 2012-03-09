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
                                                (
                                                "screen_name=user.screen_name", 
                                                "since_id=latest_status_id", 
                                                "include_rts=True", 
                                                "include_entities=True",
                                                "count=200",
                                                "page=page",
                                                ))
    return latest_statuses_page

def sleeper(retry_count):
    max_retry = 5
    retry_delay = 5
    wait_delay = retry_count*retry_delay
    wait_delay = 60 if wait_delay > 60 else wait_delay
    time.sleep(wait_delay)

def get_latest_statuses(harvester, user):

    page = 0
    retry = 0
    lsp = []
    latest_statuses = []

    while page == 0 or not lsp:
        try:
            logger.debug(u"%s:%s(%d):%d" % (harvester, unicode(user), user.fid, page))
            lsp = get_latest_statuses_page(harvester, user, page)
            if lsp:
                latest_statuses += lsp
            page += 1
            retry = 0
        except:
            msg = u"Exception for the harvester %s for the user %s(%d) at page %d" % (harvester, unicode(user), user.fid, page)
            logger.exception(msg)
            retry += 1
            if retry > harverster.max_retry_on_fail:
                page += 1
                retry = 0
            else:
                sleeper(retry_count)
    return latest_statuses

def update_user(statuses, user):
        try:
            user.update_from_twitter(statuses[0].user)
        except:
            msg = u"Cannot update user info for %s:(%d)" % (unicode(user), user.fid)
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
                msg = u"Cannot update status %s for %s:(%d)" % (unicode(status), unicode(user), user.fid)
                logger.exception(msg) 

def run_harvester_v2(harvester):

    harvester.start_new_harvest()
    user = harvester.get_next_user_to_harvest()
    while user:
        logger.info(u"Start: %s:%s(%d)" % (harvester, unicode(user), user.fid))
        ls = get_latest_statuses(harvester, user)
        update_user(ls, user)
        update_user_statuses(ls, user)
        user = harvester.get_next_user_to_harvest()
    harvester.end_current_harvest()
            
def run_harvester(harvester):
    client = twitter.Api(consumer_key=harvester.consumer_key,
                        consumer_secret=harvester.consumer_secret,
                        access_token_key=harvester.access_token_key,
                        access_token_secret=harvester.access_token_secret,
                        )
    rate = client.GetRateLimitStatus()
    if rate["remaining_hits"] == 0:
        #raise Exception("Error! No more hits with this twitter token. Need to wait! %s" % unicode(rate))
        print "Error! No more hits with this twitter token. Need to wait! %s" % unicode(rate)
        return

    userlist = harvester.twusers_to_harvest.all()
    for user in userlist:
        latest_statuses = []

        if not user.error_triggered:
            #latest_status = user.get_latest_status()
            #for now, always harvest all, all the time
            latest_status = None
            latest_status_id = 1 if latest_status is None else latest_status.fid
            latest_statuses = []
            page = 1
            retry = 0
            max_retry = 5
            retry_delay = 5

            while rate["remaining_hits"] != 0:
                rate = client.GetRateLimitStatus()
                try:
                    print page,  client.GetRateLimitStatus()["remaining_hits"]
                    latest_statuses_page = client.GetUserTimeline(
                                                                screen_name=user.screen_name, 
                                                                since_id=latest_status_id, 
                                                                include_rts=True, 
                                                                include_entities=True,
                                                                count=200,
                                                                page=page
                                                            )
                    if latest_statuses_page:
                        latest_statuses += latest_statuses_page
                    else:
                        break
                    retry = 0
                    page = page + 1

                except twitter.TwitterError, t:
                    if unicode(t) == u"Not found":
                        user.error_triggered = True
                        user.save()
                        print u"ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry." % user
                        break
                    #elif unicode(t) == u"Capacity Error":
                    retry += 1
                    if retry == max_retry:
                        raise Exception("Max retry!!! in file %s at line %s. Original err: %s"%("","",unicode(err)))
                    wait_delay = retry*retry_delay
                    wait_delay = 120 if wait_delay > 120 else wait_delay
                    print u"Waiting. Retry:",retry,u"delay:",wait_delay
                    time.sleep(wait_delay)
                    traceback.print_exc()
                    print u"ERROR:%s:" % unicode(t)
                except Exception as err:
                    print u"ERROR: %s for user %s" % (unicode(err), user)
                    retry += 1
                    if retry == max_retry:
                        raise Exception("Max retry!!! in file %s at line %s. Original err: %s"%("","",unicode(err)))
                    wait_delay = retry*retry_delay
                    wait_delay = 120 if wait_delay > 120 else wait_delay
                    print u"Waiting. Retry:",retry,u"delay:",wait_delay
                    time.sleep(wait_delay)
                    traceback.print_exc()

        else:
            print u"ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry" % user

        for tw_status in latest_statuses:
            user.update_from_twitter(tw_status.user)
            status = get_status(tw_status, user)     
        print user, u"completed"
        print_limit(client)
        print "-----------"
        print ""

def get_status(tw_status,user):
    try:
        status = TWStatus.objects.get(fid__exact=tw_status.id)
    except ObjectDoesNotExist:
        status = TWStatus()

    try:
        status.update_from_twitter(tw_status,user)
    except:
        print u"ERROR: a problem with the status. cannot be saved!!! user:%s, status id %d" %(user.screen_name, status.fid)

    return status

def print_limit(client):
    rate = client.GetRateLimitStatus()
    for elem in rate:
        print elem, rate[elem]

