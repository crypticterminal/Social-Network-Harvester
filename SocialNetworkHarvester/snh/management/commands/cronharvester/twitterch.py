# coding=UTF-8

import sys
import traceback

import twitter
import time

from django.core.exceptions import ObjectDoesNotExist

from snh.models.twitter import *

def run_twitter_harvester():
    harvester_list = TwitterHarvester.objects.all()
    for harvester in harvester_list:
        if harvester.is_active:
            run_harvester(harvester)
            
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

            while True:
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
                        raise Exception("Max retry!!! in file %s at line %s. Original err: %s"%(__file__,__line__,unicode(err)))
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
                        raise Exception("Max retry!!! in file %s at line %s. Original err: %s"%(__file__,__line__,unicode(err)))
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

