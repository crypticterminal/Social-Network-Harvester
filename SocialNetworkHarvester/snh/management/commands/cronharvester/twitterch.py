# coding=UTF-8

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

    userlist = harvester.twusers_to_harvest.all()
    for user in userlist:
        latest_statuses = []

        if not user.error_triggered:
            latest_status = user.get_latest_status()
            latest_status_id = 1 if latest_status is None else latest_status.oid
            latest_statuses = []
            page = 1
            retry = 0
            retry_delay = 30

            while True:
                try:
                    print page
                    latest_statuses_page = client.GetUserTimeline(
                                                                screen_name=user.screen_name, 
                                                                since_id=latest_status_id, 
                                                                include_rts=True, 
                                                                include_entities=True,
                                                                count=200,
                                                                page=page
                                                            )
                    page = page + 1
                    retry = 0
                    if latest_statuses_page:
                        latest_statuses += latest_statuses_page
                    else:
                        break

                except twitter.TwitterError, t:
                    if str(t) == "Not found":
                        user.error_triggered = True
                        user.save()
                        print "ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry." % user
                        break
                    elif str(t) == "Capacity Error":
                        retry += 1
                        wait_delay = retry*retry_delay
                        wait_delay = 120 if wait_delay > 120 else wait_delay
                        print "Waiting. Retry:",retry,"delay:",wait_delay
                        time.sleep(wait_delay)
                        
                    print "ERROR:%s:" % str(t)

        else:
            print "ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry" % user

        for tw_status in latest_statuses:
            user.update_from_twitter(tw_status.user)
            status = get_status(tw_status, user)     
        print user, "completed"
        print_limit(client)
        print "-----------"
        print ""
def get_status(tw_status,user):
    try:
        status = TWStatus.objects.get(oid__exact=tw_status.id)
    except ObjectDoesNotExist:
        status = TWStatus()
        try:
            status.update_from_twitter(tw_status,user)
        except:
            print "ERROR: a problem with the status. cannot be saved!!! user:%s, status id %d" %(user.screen_name, status.oid)
        #print "new", status
    return status

def print_limit(client):
    rate = client.GetRateLimitStatus()
    for elem in rate:
        print elem, rate[elem]

