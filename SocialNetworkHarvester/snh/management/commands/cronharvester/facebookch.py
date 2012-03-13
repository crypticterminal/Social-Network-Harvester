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

def get_timedelta(fb_time):
    ts = date_val = datetime.strptime(fb_time,'%Y-%m-%dT%H:%M:%S+0000')
    return (datetime.utcnow() - ts).days

def get_latest_statuses(harvester, user):

    retry = 0
    lsp = []
    latest_statuses = []

    urlid = user.fid if user.fid else user.username
    url = u"%s/feed" % urlid
    until = None
    limit = 6000
    all_status_count = 0
    while True:
        try:
            lsp_iter = harvester.api_call("get",{"path":url,"page":True,"until":until,"limit":limit})
            page = 1
            for lsp_block in lsp_iter:
                too_old = False
                
                block_len = 0
                if "data" in lsp_block:
                    block_len = len(lsp_block["data"])
                    all_status_count += block_len
                else:
                    logger.debug(u"%s:%s(%s):%d ERROR. No Block! %s" % (harvester, unicode(user), user.fid if user.fid else "0", page, lsp_block))
                
                logger.debug(u"%s:%s(%s):%d.%d;%d" % (harvester, unicode(user), user.fid if user.fid else "0", page, block_len,all_status_count))
                last_status = None
                
                for lsp in lsp_block["data"]: 
                    latest_statuses.append(lsp)
                    last_status = lsp
                    logger.debug(u"%s:%s(%s):%d" % (harvester, unicode(user), user.fid if user.fid else "0", lsp["id"]))
                    if get_timedelta(last_status["created_time"]) >= harvester.dont_harvest_further_than:
                        break

                if not last_status:
                    logger.debug(u"%s:%s(%s):%d.No more status?" % (harvester, unicode(user), user.fid if user.fid else "0", page))
                    break
                elif get_timedelta(last_status["created_time"]) >= harvester.dont_harvest_further_than:
                    logger.debug(u"%s:%s(%s). max date reached. Now:%s, Status.created_at:%s, Delta:%s" % 
                                                                    (harvester, 
                                                                    unicode(user), 
                                                                    user.fid if user.fid else 0, 
                                                                    datetime.utcnow(), 
                                                                    datetime.strptime(last_status["created_time"],'%Y-%m-%dT%H:%M:%S+0000'),
                                                                    get_timedelta(last_status["created_time"]),
                                                                    ))
                    break

                page += 1
                logger.debug(u"%s:%s(%s): Will fetch page %d" % (harvester, unicode(user), user.fid if user.fid else "0", page))
            break
        except FacepyError, fex:
            (retry, need_a_break) = manage_facebook_exception(retry, harvester, user, fex)
            if need_a_break:
                break
            else:
                sleeper(retry)   
        except:
            (retry, need_a_break) = manage_exception(retry, harvester, user)
            if need_a_break:
                break
            else:
                sleeper(retry)   
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

def get_comments(harvester, status, user, count, total):
    page = 1
    retry = 0
    lc = []
    latest_comments = []
    until = None
    limit = 6000

    url = u"%s/comments" % status.fid
    while True:
        try:
            lc_iter = harvester.api_call("get",{"path":url,"page":True,"until":until,"limit":limit})
            for lc_block in lc_iter:
                logger.debug(u"%s-%s:%s:%d/%d:%d" % (harvester, unicode(user), status.fid if status.fid else "0",count, total, page))
                subpage = 0

                for lc in lc_block["data"]:
                    logger.debug(u"%s-%s:%s:%d/%d:%d.%d" % (harvester, unicode(user), status.fid if status.fid else "0", count, total, page, subpage))
                    latest_comments.append(lc)
                    subpage += 1
                page += 1
            break
        except FacepyError, fex:
            (retry, need_a_break) = manage_facebook_exception(retry, harvester, status, fex)
            if need_a_break:
                break
            else:
                sleeper(retry)   
        except:
            (retry, need_a_break) = manage_exception(retry, harvester, status)
            if need_a_break:
                break
            else:
                sleeper(retry)   

    return latest_comments

def update_comment(harvester, status, user, count, total):
    
    comments = get_comments(harvester, status, user, count, total)
    logger.debug(u"%s-%s:%s %d/%d.Adding (%d) comments to db." % (harvester, unicode(user), status.fid if status.fid else "0", count, total, len(comments)))
    for comment in comments:
        try:
            try:
                fb_comment = FBComment.objects.get(fid__exact=comment["id"])
            except ObjectDoesNotExist:
                fb_comment = FBComment()
            fb_comment.update_from_facebook(comment,status)                
        except:
            msg = u"%s-%s:%s %d/%d.Cannot update comment %s for %s:(%s)" % (harvester, unicode(user), status.fid if status.fid else "0", count, total, unicode(status), unicode(fb_comment), fb_comment.fid if fb_comment.fid else "0")
            logger.exception(msg) 

def update_user_statuses(harvester, statuses, user):
        status_count = 1
        total_status = len(statuses)
        for status in statuses:
            try:
                try:
                    fb_status = FBPost.objects.get(fid__exact=status["id"])
                except ObjectDoesNotExist:
                    fb_status = FBPost(user=user)
                    fb_status.save()

                fb_status.update_from_facebook(status,user)
                if fb_status.comments_count > 0:
                    update_comment(harvester, fb_status, user, status_count, total_status)
                    
            except:
                msg = u"Cannot update status %s for %s:(%s)" % (unicode(status), unicode(user), user.fid if user.fid else "0")
                logger.exception(msg) 
            status_count += 1

def run_harvester_v2(harvester):
    harvester.start_new_harvest()
    user = harvester.get_next_user_to_harvest()
    #logger.info(u"START: %s Stats:%s" % (harvester, harvester.get_stats())   )
    try:
        while user:
            if not user.error_triggered:
                logger.info(u"Start: %s:%s(%s)." % (harvester, unicode(user), user.fid if user.fid else "0"))

                fbuser = get_user(harvester, user)
                ls = get_latest_statuses(harvester, user)
                retry = 0
                while True:
                    try:
                        user.update_from_facebook(fbuser)
                        update_user_statuses(harvester, ls, user)
                        break
                    except:
                        (retry, need_a_break) = manage_exception(retry, harvester, user)
                        if need_a_break:
                            break
                        else:
                            sleeper(retry)   

            else:
                logger.info(u"Skipping: %s:%s(%s) because user has triggered the error flag." % (harvester, unicode(user), user.fid if user.fid else "0"))
            user = harvester.get_next_user_to_harvest()
    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))

