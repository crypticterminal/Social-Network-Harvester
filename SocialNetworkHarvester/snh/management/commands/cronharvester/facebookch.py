# coding=UTF-8

import urlparse
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

def run_harvester(harvester):
    fanuser = FanUser.objects.all()[0]
    userlist = harvester.fbusers_to_harvest.all()

    for user in userlist:
        latest_posts = []

        if not user.error_triggered:
            url = "%s/feed" % user.username
            update_user = None
            latest_posts = []
            page = 0
            retry = 0
            retry_delay = 5
            until = None
            limit = None
            while True:
                try:
                    print user.username, page
                    if not update_user:
                        update_user = fanuser.graph.get(user.username)
                        user.update_from_facebook(update_user)
                    latest_posts_page = fanuser.graph.get(url,until=until, limit=limit)
                    until,limit = get_paging(latest_posts_page)
                    page = page + 1
                    if latest_posts_page["data"]:
                        latest_posts += latest_posts_page["data"]
                    else:
                        break

                except FacepyError as err:
                    if str(err).startswith("(#803)"):
                        user.error_triggered = True
                        user.save()
                        print "ERROR: the user %s was reject: %s. Please remove the error_triggered flag to retry." % (user, err)
                    elif str(err).startswith("Unknown path components:"):
                        print "ERROR: %s for user %s. EXITING!!!" % (err, user)
                        break                    
                    else:
                        print "ERROR: %s for user %s" % (err, user)
                        retry += 1
                        wait_delay = retry*retry_delay
                        wait_delay = 120 if wait_delay > 120 else wait_delay
                        print "Waiting. Retry:",retry,"delay:",wait_delay
                        time.sleep(wait_delay)

            #for post in latest_posts:
            #    print_post(post)

        else:
            print "ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry" % user

        for fb_post in latest_posts:
            post = update_post(fb_post, user)
        print user, "completed"
        print "-----------"
        print ""

def update_post(fb_post, user):
    fid = fb_post["id"]

    try:
        post = FBPost.objects.get(fid__exact=fid)
        print "exists"
    except ObjectDoesNotExist:
        post = FBPost()

    post.update_from_facebook(fb_post, user)

    return post


def td(d,v):
    if v in d:
        return d[v]
    else:
        return None
     
def print_post(data):
    keys = [
            "id",
            "from",
            "to",
            "message",
            "message_tags",
            "picture",
            "link",
            "name",
            "caption",
            "description",
            "source",
            "properties",
            "icon",
            "actions",
            "privacy",
            "type",
            "likes",
            "place",
            "story",
            "story_tags",
            "comments",
            "object_id",
            "created_time",
            "updated_time",
            "shares",
            ]

    for key in keys:
        if td(data, key):
            print key+":", td(data, key)

    if "comments" in data:
        print "comments count:", data["comments"]

    if "likes" in data:
        print "likes count:", data["likes"]

    if "shares" in data:
        print "shares count:", data["shares"]["count"]

    if "from" in data:
        print "from:", data["from"]["name"]
    print "------------"

def get_paging(page):
    until = None
    limit = None
    if "paging" in page and "next" in page["paging"]:
        url = urlparse.parse_qs(page["paging"]["next"])
        until = url["until"][0]
        limit = url["limit"][0]
    return until, limit

