# coding=UTF-8

from fandjango.models import User as FanUser
from django.core.exceptions import ObjectDoesNotExist
import facepy
from facepy.exceptions import FacepyError

from snh.models.facebook import *


def run_facebook_harvester():
    harvester_list = FacebookHarvester.objects.all()
    for harvester in harvester_list:
        if harvester.is_active:
            run_harvester(harvester)

def td(d,v):
    if v in d:
        return d[v]
    else:
        return None
     
def parsedata(data):
    keys = ["id","type", "picture","source","name","link", "message", "created_time","updated_time", "description", "caption" ]
    for key in keys:
        print key+":", td(data, key)

    if "comments" in data:
        print "comments count:", data["comments"]

    if "likes" in data:
        print "likes count:", data["likes"]
    else:
        print "no likes"

    if "shares" in data:
        print "shares count:", data["shares"]["count"]
    else:
        print "no shares"

    if "from" in data:
        print "from:", data["from"]["name"]
    else:
        print "no from"
    print "------------"
       
def run_harvester(harvester):
    fanuser = FanUser.objects.all()[0]
    userlist = harvester.fbusers_to_harvest.all()

    for user in userlist:
        latest_statuses = []

        if not user.error_triggered:
            url = "%s/feed" % user.username
            print url
            latest_statuses = []
            page = 1
            retry = 0
            retry_delay = 30

            while True:
                try:
                    latest_statuses_page = fanuser.graph.get(url,limit=100,offset=page)
                    page = page + 1
                    if latest_statuses_page["data"]:
                        for status in latest_statuses_page["data"]:
                            print "INFO:",status["updated_time"], status["from"]["name"], status["type"]
                            if "message" in status: print "MESSAGE:", status["message"]
                            print "---------"
                            break
                        latest_statuses += latest_statuses_page["data"]
                    else:
                        break

                except FacepyError as err:
                    if str(err).startswith("(#803)"):
                        user.error_triggered = True
                        user.save()
                        print "ERROR: the user %s was reject: %s. Please remove the error_triggered flag to retry." % (user, err)
                    else:
                        print "ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry" % user
                        print "ERROR:",err

            #if latest_statuses["data"]:
            #    for status in latest_statuses["data"]:
            #        print status["updated_time"], status["message"]


            #latest_status = user.get_latest_status()
            #latest_status_id = 1 if latest_status is None else latest_status.oid
            #latest_statuses = []
            #page = 1
            #retry = 0
            #retry_delay = 30

            #while True:
            #    try:
            #        print page
            #        latest_statuses_page = client.GetUserTimeline(
            #                                                    screen_name=user.screen_name, 
            #                                                    since_id=latest_status_id, 
            #                                                    include_rts=True, 
            #                                                    include_entities=True,
            #                                                    count=200,
            #                                                    page=page
            #                                                )
            #        page = page + 1
            #        if latest_statuses_page:
            #            latest_statuses += latest_statuses_page
            #        else:
            #            break
            #
            #    except twitter.TwitterError, t:
            #        if str(t) == "Not found":
            #            user.error_triggered = True
            #            user.save()
            #            print "ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry." % user
            #            break
            #        elif str(t) == "Capacity Error":
            #            retry += 1
            #            wait_delay = retry*retry_delay
            #            wait_delay = 120 if wait_delay > 120 else wait_delay
            #            print "Waiting. Retry:",retry,"delay:",wait_delay
            #            time.sleep(wait_delay)
            #            
            #        print "ERROR:%s:" % str(t)

        else:
            print "ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry" % user

        #for tw_status in latest_statuses:
        #    user.update_from_twitter(tw_status.user)
        #    status = get_status(tw_status, user)     
        print user, "completed"
        #print_limit(client)
        print "-----------"
        print ""

def get_status(tw_status,user):
    try:
        status = TWStatus.objects.get(oid__exact=tw_status.id)
    except ObjectDoesNotExist:
        status = TWStatus()
        status.update_from_twitter(tw_status,user)
        #print "new", status
    return status


