# coding=UTF-8

import sys
import time

from django.core.exceptions import ObjectDoesNotExist
from facepy.exceptions import FacepyError
from fandjango.models import User as FanUser
from snh.models.facebookmodel import *

import snhlogger
logger = snhlogger.init_logger(__name__, "facebook.log")

def run_facebook_harvester():
    harvester_list = FacebookHarvester.objects.all()
    fanuser = FanUser.objects.all()[0]
    for harvester in harvester_list:
        harvester.set_client(fanuser.graph)
        logger.info(u"The harvester %s is %s" % 
                                                (unicode(harvester), 
                                                "active" if harvester.is_active else "inactive"))
        if harvester.is_active:
            run_harvester_v2(harvester)

def sleeper(retry_count):
    max_retry = 5
    retry_delay = 1
    wait_delay = retry_count*retry_delay
    wait_delay = 60 if wait_delay > 60 else wait_delay
    time.sleep(wait_delay)

def manage_exception(retry_count, harvester, user):
    msg = u"Exception for the harvester %s for the user %s(%s). Retry:%d" % (harvester, unicode(user), user.fid if user.fid else "0", retry_count)
    logger.exception(msg)
    retry_count += 1
    return (retry_count, retry_count > harvester.max_retry_on_fail)

def manage_facebook_exception(retry_count, harvester, user, fex):
    retry_count += 1
    need_a_break = retry_count > harvester.max_retry_on_fail

    if unicode(fex).startswith(u"(#803)"):
        user.error_triggered = True
        user.save()
        msg = u"Exception for the harvester %s for the user %s(%s). Retry:%d. The user does not exists!" % (harvester, unicode(user), user.fid if user.fid else "0", retry_count)
        logger.exception(msg)
        need_a_break = True
    elif unicode(fex).startswith("Unknown path components:"):
        msg = u"Exception for the harvester %s for the user %s(%s). Retry:%d. The user does not exists!" % (harvester, unicode(user), user.fid if user.fid else "0", retry_count)
        logger.exception(msg)
        need_a_break = True                    
    else:
        msg = u"Exception for the harvester %s for the user %s(%s). Retry:%d. The user does not exists!" % (harvester, unicode(user), user.fid if user.fid else "0", retry_count)
        logger.exception(msg)

    return (retry_count, retry_count > harvester.max_retry_on_fail)

def get_latest_statuses(harvester, user):

    page = 1
    retry = 0
    lsp = []
    latest_statuses = []

    urlid = user.fid if user.fid else user.username
    url = u"%s/feed" % urlid
    until = None
    limit = None

    try:
        lsp_iter = harvester.api_call("get",{"path":url,"page":True,"until":until,"limit":limit})
        for lsp_block in lsp_iter:
            logger.debug(u"%s:%s(%s):%d" % (harvester, unicode(user), user.fid if user.fid else "0", page))
            for lsp in lsp_block["data"]: 
                latest_statuses.append(lsp)
            page += 1

    except FacepyError, fex:
        (retry, need_a_break) = manage_facebook_exception(retry, harvester, user, fex)
    except:
        (retry, need_a_break) = manage_exception(retry, harvester, user)

    return latest_statuses

def get_user(harvester, user):

    urlid = user.fid if user.fid else user.username
    url = u"%s" % urlid
    fbuser = None

    try:
        fbuser = harvester.api_call("get",{"path":url})
    except FacepyError, fex:
        (retry, need_a_break) = manage_facebook_exception(retry, harvester, user, fex)
    except:
        (retry, need_a_break) = manage_exception(retry, harvester, user)

    return fbuser

def get_comments(harvester, status):
    page = 1
    retry = 0
    lc = []
    latest_comments = []

    url = u"%s/comments" % status.fid

    try:
        lc_iter = harvester.api_call("get",{"path":url,"page":True,})
        for lc_block in lc_iter:
            logger.debug(u"%s:%s(%s):%d" % (harvester, unicode(status), status.fid if status.fid else "0", page))
            for lc in lc_block["data"]:
                latest_comments.append(lc)
            page += 1

    except FacepyError, fex:
        (retry, need_a_break) = manage_facebook_exception(retry, harvester, status, fex)
    except:
        (retry, need_a_break) = manage_exception(retry, harvester, status)

    return latest_comments

def update_comment(harvester, status):
    
    comments = get_comments(harvester, status)

    for comment in comments:
        try:
            try:
                fb_comment = FBComment.objects.get(fid__exact=comment["id"])
            except ObjectDoesNotExist:
                fb_comment = FBComment()
            fb_comment.update_from_facebook(comment,status)
                
        except:
            msg = u"Cannot update comment %s for %s:(%s)" % (unicode(status), unicode(comment), comment.fid if comment.fid else "0")
            logger.exception(msg) 


def update_user_statuses(harvester, statuses, user):
        for status in statuses:
            try:
                try:
                    fb_status = FBPost.objects.get(fid__exact=status["id"])
                except ObjectDoesNotExist:
                    fb_status = FBPost()
                fb_status.update_from_facebook(status,user)
                if fb_status.comments_count > 0:
                    update_comment(harvester, fb_status)
                    
            except:
                msg = u"Cannot update status %s for %s:(%s)" % (unicode(status), unicode(user), user.fid if user.fid else "0")
                logger.exception(msg) 

def run_harvester_v2(harvester):
    harvester.start_new_harvest()
    user = harvester.get_next_user_to_harvest()
    #logger.info(u"START: %s Stats:%s" % (harvester, harvester.get_stats())   )
    try:
        while user:
            if not user.error_triggered:
                logger.info(u"Start: %s:%s(%s)." % (harvester, unicode(user), user.fid if user.fid else "0"))

                fbuser = get_user(harvester, user)
                user.update_from_facebook(fbuser)
                ls = get_latest_statuses(harvester, user)
                update_user_statuses(harvester, ls, user)
            else:
                logger.info(u"Skipping: %s:%s(%s) because user has triggered the error flag." % (harvester, unicode(user), user.fid if user.fid else "0"))
            user = harvester.get_next_user_to_harvest()
    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))





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

def get_msg(data):

    if td(data, u"message"):
        return  td(data,  u"message")
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

