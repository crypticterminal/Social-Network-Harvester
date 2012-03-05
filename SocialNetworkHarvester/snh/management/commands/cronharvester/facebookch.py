# coding=UTF-8

import sys
import traceback

import codecs
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
            urlid = user.fid if user.fid else user.username
            url = u"%s/feed" % urlid
            update_user = None
            latest_posts = []
            page = 0
            retry = 0
            retry_delay = 5
            max_retry = 10
            until = None
            limit = None
            while True:
                try:
                    print user.username, page
                    if not update_user:
                        update_user = fanuser.graph.get(urlid)
                        user.update_from_facebook(update_user)
                    latest_posts_page = fanuser.graph.get(url,until=until, limit=limit)
                    if "data" in latest_posts_page and latest_posts_page["data"]:
                        latest_posts += latest_posts_page["data"]
                    else:
                        break
                    until,limit = get_paging(latest_posts_page)
                    retry = 0
                    page = page + 1

                except FacepyError as err:
                    unierr = unicode(err)
                    if unierr.startswith(u"(#803)"):
                        user.error_triggered = True
                        user.save()
                        print u"ERROR: the user %s was reject: %s. Please remove the error_triggered flag to retry." % (user, unierr)
                        break
                    elif unicode(err).startswith("Unknown path components:"):
                        print u"ERROR: %s for user %s. EXITING!!!" % (unicode(err), user)
                        break                    
                    else:
                        print u"ERROR: %s for user %s" % (unicode(err), user)
                        retry += 1
                        if retry == max_retry:
                            raise Exception("Max retry!!! in file %s at line %s. Original err: %s"%(__file__,__line__,unicode(err)))
                        wait_delay = retry*retry_delay
                        wait_delay = 120 if wait_delay > 120 else wait_delay
                        print u"Waiting. Retry:",retry,u"delay:",wait_delay
                        time.sleep(wait_delay)
                        traceback.print_exc()
                except KeyError as err:
                        print u"ERROR: %s for user %s. %s" % (unicode(err), user, unicode(latest_posts_page) )
                        retry += 1
                        if retry == max_retry:
                        #    raise Exception("Max retry!!! in file %s at line %s. Original err: %s"%(__file__,__line__,unicode(err)))
                            until,limit = get_paging(latest_posts_page)
                            retry = 0
                            page = page + 1
                        wait_delay = retry*retry_delay
                        wait_delay = 120 if wait_delay > 120 else wait_delay
                        print u"Waiting. Retry:",retry,u"delay:",wait_delay
                        time.sleep(wait_delay)
                        traceback.print_exc()
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

        for fb_post in latest_posts:
            post = update_post(fb_post, user)
        print user, u"completed"
        print "-----------"
        print ""


def update_post(fb_post, user):
    fid = fb_post["id"]

    try:
        post = FBPost.objects.get(fid__exact=fid)
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
            u"id",
            u"from",
            u"to",
            u"message",
            u"message_tags",
            u"picture",
            u"link",
            u"name",
            u"caption",
            u"description",
            u"source",
            u"properties",
            u"icon",
            u"actions",
            u"privacy",
            u"type",
            u"likes",
            u"place",
            u"story",
            u"story_tags",
            u"comments",
            u"object_id",
            u"created_time",
            u"updated_time",
            u"shares",
            ]

    for key in keys:
        if td(data, key):
            print key+":", td(data, key)

    if u"comments" in data:
        print u"comments count:", data[u"comments"]

    if u"likes" in data:
        print u"likes count:", data[u"likes"]

    if u"shares" in data:
        print u"shares count:", data[u"shares"][u"count"]

    if u"from" in data:
        print u"from:", data[u"from"][u"name"]
    print "------------"

def get_paging(page):
    until = None
    limit = None
    if u"paging" in page and u"next" in page[u"paging"]:
        url = urlparse.parse_qs(page[u"paging"][u"next"])
        until = url[u"until"][0]
        limit = url[u"limit"][0]
    return until, limit

