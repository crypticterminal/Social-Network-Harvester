# coding=UTF-8

import sys
import time
import urlparse
import resource
import json

from datetime import timedelta

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
            run_harvester_v3(harvester)

def sleeper(retry_count):
    retry_delay = 10
    wait_delay = retry_count*retry_delay
    wait_delay = 60 if wait_delay > 60 else wait_delay
    time.sleep(wait_delay)

def manage_exception(retry_count, harvester, related_object):
    msg = u"Exception for the harvester %s for the object %s. Retry:%d" % (harvester, 
                                                                                unicode(related_object), 
                                                                                retry_count)
    logger.exception(msg)
    retry_count += 1
    return (retry_count, retry_count > harvester.max_retry_on_fail)

def manage_facebook_exception(retry_count, harvester, related_object, fex):
    retry_count += 1

    if unicode(fex).startswith(u"(#803)"):
        user.error_triggered = True
        user.save()
        msg = u"Exception for the harvester %s for the object %s. Retry:%d. The user does not exists!" % (harvester, 
                                                                                                                unicode(related_object), 
                                                                                                                retry_count)
        logger.exception(msg)
        need_a_break = True
    elif unicode(fex).startswith("Unknown path components:"):
        msg = u"Exception for the harvester %s for the object %s. Retry:%d. Unknown path components." % (harvester, 
                                                                                                                unicode(related_object), 
                                                                                                                retry_count)
        logger.exception(msg)
        need_a_break = True                    
    else:
        msg = u"Exception for the harvester %s for the object %s. Retry:%d. Unknown facepy exception!" % (harvester, 
                                                                                                                unicode(related_object), 
                                                                                                                retry_count)
        logger.exception(msg)

    return (retry_count, retry_count > harvester.max_retry_on_fail)

def get_timedelta(fb_time):
    ts = date_val = datetime.strptime(fb_time,'%Y-%m-%dT%H:%M:%S+0000')
    return (datetime.utcnow() - ts).days


def get_status_paging(page):
    until = None
    new_page = False
    if u"paging" in page and u"next" in page[u"paging"]:
        url = urlparse.parse_qs(page[u"paging"][u"next"])
        until = url[u"until"][0]
        new_page = True
        url = None
    return ["until",until], new_page

def get_comment_paging(page):
    __after_id = None
    new_page = False
    if u"paging" in page and u"next" in page[u"paging"]:
        url = urlparse.parse_qs(page[u"paging"][u"next"])
        __after_id = url[u"__after_id"][0]
        new_page = True
    return ["__after_id",__after_id], new_page

def get_timedelta(fb_time):
    ts = datetime.strptime(fb_time,'%Y-%m-%dT%H:%M:%S+0000')
    return (datetime.utcnow() - ts).days

#def get_facebook_list(harvester, url, related_object, page_func, history_limit=True):
#    complete_list = []
#    page = 0
#    retry = 0
#    until = ["until",None]
#    limit = 6000
#    while True:
#        try:
#            usage = resource.getrusage(resource.RUSAGE_SELF)
#            logger.info(u"%s %s page:%d retry:%d Mem:%s KB" % (harvester, related_object, page, retry, unicode(getattr(usage, "ru_maxrss")/(1024.0))))
#            latest_page = harvester.api_call("get",{"path":url,until[0]:until[1],"limit":limit})
#            delta = 0
#            last_post_time = ""
#            max_age_reached = False#
#
#            if "data" in latest_page and latest_page["data"]:
#                logger.debug(u"%s %s page:%d retry:%d adding: %d objects" % (harvester, 
#                                                                                        related_object, 
#                                                                                        page, 
#                                                                                        retry, 
#                                                                                        len(latest_page["data"])))
#                for data in latest_page["data"]:
#                    last_post_time = data["created_time"]
#                    delta = get_timedelta(last_post_time)
#                    if delta >= harvester.dont_harvest_further_than:
#                        max_age_reached = True
#                    else:
#                        complete_list.append(data)
#                
#            else:
#                logger.debug(u"%s %s page:%d retry:%d No more data?" % (harvester, 
#                                                                                    related_object, 
#                                                                                    page, 
#                                                                                    retry, 
#                                                                                    ))
#                break#
#
#            if max_age_reached:
#                logger.debug(u"%s %s page:%d retry:%d Max age reached. now:%s then:%s delta:%s" % (harvester, 
#                                                                                    related_object, 
#                                                                                    page, 
#                                                                                    retry, 
#                                                                                    datetime.utcnow(),
#                                                                                    last_post_time,
#                                                                                    delta,
#                                                                                    ))
#                break#
#
#            until, new_page = page_func(latest_page)
#            if not new_page:
#                logger.debug(u"%s %s page:%d retry:%d No new page?" % (harvester, 
#                                                                                    related_object, 
#                                                                                    page, 
#                                                                                    retry, 
#                                                                                    ))
#                break#
#
#            retry = 0
#            page += 1
#            latest_page = None##
#
#        except FacepyError, fex:
#            (retry, need_a_break) = manage_facebook_exception(retry, harvester, related_object, fex)
#            if need_a_break:
#                logger.debug(u"%s %s page:%d retry:%d FacepyError:breaking, too many retry!" % (harvester, 
#                                                                                                            related_object, 
#                                                                                                            page, 
#                                                                                                            retry, 
#                                                                                                ))
#                break
#            else:
#                sleeper(retry)
#        except:
#            (retry, need_a_break) = manage_exception(retry, harvester, related_object)
#            if need_a_break:
#                logger.debug("u%s %s page:%d retry:%d Error:breaking, too many retry!" % (harvester, 
#                                                                                                    related_object, 
#                                                                                                    page, 
#                                                                                                    retry, 
#                                                                                            ))
#                break
#            else:
#                sleeper(retry)
#    return complete_list

#def get_latest_statuses(harvester, user):#
#
#    urlid = user.fid if user.fid else user.username
#    url = u"%s/feed" % urlid
#    usage = resource.getrusage(resource.RUSAGE_SELF)
#    logger.debug(u"%s %s %s Will get statuses. Mem:%sKB" % (harvester, user, url,unicode(getattr(usage, "ru_maxrss")/(1024.0))))
#    latest_statuses = get_facebook_list(harvester, url, user, get_status_paging)
#    return latest_statuses

#def get_user(harvester, user):#
#
#    urlid = user.fid if user.fid else user.username
#    url = u"%s" % urlid
#    logger.debug(u"%s %s %s Will get user" % (harvester, user, url))
#    fbuser = None
#    retry = 0#
#
#    while True:
#        try:
#            fbuser = harvester.api_call("get",{"path":url})
#            break
#        except FacepyError, fex:
#            (retry, need_a_break) = manage_facebook_exception(retry, harvester, user, fex)
#            if need_a_break:
#                logger.debug(u"%s %s retry:%d FacepyError:breaking, too many retry!" % (harvester, 
#                                                                                        user, 
#                                                                                        retry, 
#                                                                                        ))
#                break
#            else:
#                sleeper(retry)   
#        except:
#            (retry, need_a_break) = manage_exception(retry, harvester, user)
#            if need_a_break:
#                logger.debug("u%s %s retry:%d Error:breaking, too many retry!" % (harvester, 
#                                                                                    user, 
#                                                                                    retry, 
#                                                                                    ))
#                break
#            else:
#                sleeper(retry)
#    return fbuser

#def get_comments(harvester, status, user, count, total):#
#
#    latest_comments = []
#    url = u"%s/comments" % status.fid
#    usage = resource.getrusage(resource.RUSAGE_SELF)
#    logger.debug(u"%s %s %s Will get comment. Mem:%s KB" % (harvester, user, url,unicode(getattr(usage, "ru_maxrss")/(1024.0))))
#    latest_comments = get_facebook_list(harvester, url, status, get_comment_paging)
#    return latest_comments

#def update_comment(harvester, status, user, count, total):
#    
#    comments = get_comments(harvester, status, user, count, total)
#    logger.debug(u"%s-%s:%s %d/%d.Adding (%d) comments to db." % (harvester, unicode(user), status.fid if status.fid else "0", count, total, len(comments)))
#    for comment in comments:
#        try:
#            try:
#                fb_comment = FBComment.objects.get(fid__exact=comment["id"])
#            except ObjectDoesNotExist:
#                fb_comment = FBComment()
#            fb_comment.update_from_facebook(comment,status)                
#        except:
#            msg = u"%s-%s:%s %d/%d.Cannot update comment %s for %s:(%s)" % (harvester, unicode(user), status.fid if status.fid else "0", count, total, unicode(status), unicode(fb_comment), fb_comment.fid if fb_comment.fid else "0")
#            logger.exception(msg) 

def update_user_statuses(harvester, statuses, snhuser):
    for status in statuses:
        try:
            try:
                fb_status = FBPost.objects.get(fid__exact=status["id"])
                logger.error(u"STATUS EXISTS!!!! %s" % status["id"])
            except ObjectDoesNotExist:
                fb_status = FBPost(user=snhuser)
                fb_status.save()
            fb_status.update_from_facebook(status,snhuser)
        except:
            msg = u"Cannot update status %s for %s:(%s)" % (unicode(status), unicode(snhuser), snhuser.fid if snhuser.fid else "0")
            logger.exception(msg) 

def build_json_user_batch(user_batch):
    py_batch = []
    batch_man = []
    for snhuser in user_batch:
        if not snhuser.error_triggered:
            uid = snhuser.fid if snhuser.fid else snhuser.username
            d = {"method": "GET", "relative_url": u"%s" % unicode(uid)}
            py_batch.append(d)
            batch_man.append({"snh_obj":snhuser,"retry":0})
        else:
            logger.info(u"Skipping: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))
    json_batch = json.dumps(py_batch)
    return json_batch, batch_man


def manage_error_from_batch(harvester, bman, fbobj):

    need_a_break = False
    error = unicode(fbobj).split(":")[1].strip()
    snh_obj = bman["snh_obj"]

    if unicode(error).startswith(u"(#803)"):
        snh_obj.error_triggered = True
        snh_obj.save()
        need_a_break = True
        msg = u"The object does not exists. snh_user:%s" % (unicode(snh_obj))
        logger.error(msg)
    elif unicode(error).startswith("Unknown path components:"):
        msg = u"Unknown path components for %s. Error:%s" %(unicode(snh_obj), fanobj)
        logger.error(msg)
        need_a_break = True                    

    bman["retry"] += 1
    if bman["retry"] > harvester.max_retry_on_fail:
        msg = u"Max retry for %s. Error:%s" %(unicode(snh_obj), fbobj)
        logger.error(msg)
        need_a_break = True                   
    
    return need_a_break

def generic_batch_processor(harvester, bman_list, update_func):

    step_size = 50
    next_bman_list = []

    while bman_list:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.info(u"New batch: %s Mem:%s KB" % (harvester,unicode(getattr(usage, "ru_maxrss")/(1024.0))))
        split_bman = [bman_list[i:i+step_size] for i  in range(0, len(bman_list), step_size)]
        for bman in split_bman:
            retry = 0
            while True:
                try:
                    usage = resource.getrusage(resource.RUSAGE_SELF)
                    logger.debug(u"New bman: len:%s retry:%d Mem:%s KB" % (len(bman), retry, getattr(usage, "ru_maxrss")/(1024.0)))
                    next_bman_list = []
                    obj_pos = 0
                    pyb = [bman[j]["request"] for j in range(0, len(bman))]
                    batch_result = harvester.api_call("batch",{"batch":json.dumps(pyb)})
                    for fbobj in batch_result:
                        bman_obj = bman[obj_pos]
                        if type(fbobj) == type(dict()):
                            next = update_func(harvester, bman_obj["snh_obj"], fbobj)
                            if next:
                                next_bman_list.append(next)
                        else:
                            if not manage_error_from_batch(harvester, bman_obj, fbobj):
                                next_bman_list.append(bman_obj)
                        obj_pos += 1
                    break
                except FacepyError, fex:
                    (retry, need_a_break) = manage_facebook_exception(retry, harvester, bman, fex)
                    if need_a_break:
                        logger.warning(u"%s %s retry:%d FacepyError:breaking, too many retry!" % (harvester, 
                                                                                                bman, 
                                                                                                retry, 
                                                                                                ))
                        break
                    else:
                        sleeper(retry)
                except:
                    (retry, need_a_break) = manage_exception(retry, harvester, bman)
                    if need_a_break:
                        logger.warning("u%s %s retry:%d Error:breaking, too many retry!" % (harvester, 
                                                                                            bman, 
                                                                                            retry, 
                                                                                            ))
                        break
                    else:
                        sleeper(retry)
        bman_list = next_bman_list

def update_user_from_batch(harvester, snhuser, fbuser):
    snhuser.update_from_facebook(fbuser)
    return None

def update_user_batch(harvester):

    all_users = harvester.fbusers_to_harvest.all()
    batch_man = []

    for snhuser in all_users:
        if not snhuser.error_triggered:
            uid = snhuser.fid if snhuser.fid else snhuser.username
            d = {"method": "GET", "relative_url": u"%s" % unicode(uid)}
            batch_man.append({"snh_obj":snhuser,"retry":0,"request":d})
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    generic_batch_processor(harvester, batch_man, update_user_from_batch)

def update_user_status_from_batch(harvester, snhuser, fbstatus_page):
    next_bman = None
    status_count = len(fbstatus_page["data"])

    if status_count:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.debug(u"Updating %d statuses: %s Mem:%s KB" % (status_count, harvester, unicode(getattr(usage, "ru_maxrss")/(1024.0))))

        update_user_statuses(harvester, fbstatus_page["data"], snhuser)
        paging, new_page = get_status_paging(fbstatus_page)

        delta = get_timedelta(fbstatus_page["data"][status_count-1]["created_time"])

        if new_page and delta < harvester.dont_harvest_further_than:
            d = {"method": "GET", "relative_url": u"%s/feed?limit=6000&%s=%s" % (unicode(snhuser.fid), paging[0], paging[1])}
            next_bman = {"snh_obj":snhuser,"retry":0,"request":d}

    return next_bman

def update_user_statuses_batch(harvester):

    all_users = harvester.fbusers_to_harvest.all()
    batch_man = []

    for snhuser in all_users:
        if not snhuser.error_triggered:
            uid = snhuser.fid if snhuser.fid else snhuser.username
            d = {"method": "GET", "relative_url": u"%s/feed?limit=6000" % unicode(uid)}
            batch_man.append({"snh_obj":snhuser,"retry":0,"request":d})
        else:
            logger.info(u"Skipping status update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    generic_batch_processor(harvester, batch_man, update_user_status_from_batch)

def update_user_comments(harvester, fbcomments, status):
    for fbcomment in fbcomments:
        try:
            try:
                snh_comment = FBComment.objects.get(fid__exact=fbcomment["id"])
                logger.error(u"COMMENT EXISTS!!!! %s" % fbcomment["id"])
            except ObjectDoesNotExist:
                snh_comment = FBComment()
                snh_comment.save()
            snh_comment.update_from_facebook(fbcomment, status)                
        except:
            msg = u"Cannot update comment %s for status %s" % (fbcomment, status.fid if status.fid else "0")
            logger.exception(msg) 

def update_user_comments_from_batch(harvester, status, fbcomments_page):
    next_bman = None
    comment_count = len(fbcomments_page["data"])

    if comment_count:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.debug(u"Updating %d comments: %s Mem:%s KB" % (comment_count, harvester, unicode(getattr(usage, "ru_maxrss")/(1024.0))))

        update_user_comments(harvester, fbcomments_page["data"], status)
        paging, new_page = get_comment_paging(fbcomments_page)

        delta = get_timedelta(fbcomments_page["data"][comment_count-1]["created_time"])

        if new_page and delta < harvester.dont_harvest_further_than:
            d = {"method": "GET", "relative_url": u"%s/comments?limit=6000&%s=%s" % (unicode(status.fid), paging[0], paging[1])}
            next_bman = {"snh_obj":status,"retry":0,"request":d}
        
    return next_bman

def update_user_comments_batch(harvester):

    all_users = harvester.fbusers_to_harvest.all()
    batch_man = []

    for snhuser in all_users:
        if not snhuser.error_triggered:
            not_further_than = datetime.utcnow() - timedelta(days=harvester.dont_harvest_further_than)
            all_user_statuses = FBPost.objects.filter(created_time__lt=not_further_than)
            for status in all_user_statuses:
                d = {"method": "GET", "relative_url": u"%s/comments?limit=6000" % unicode(status.fid)}
                batch_man.append({"snh_obj":status,"retry":0,"request":d})
                
        else:
            logger.info(u"Skipping comments update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    generic_batch_processor(harvester, batch_man, update_user_comments_from_batch)


def run_harvester_v3(harvester):
    harvester.start_new_harvest()
    try:
        update_user_batch(harvester)
        update_user_statuses_batch(harvester)
        update_user_comments_batch(harvester)
    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s Mem:%s KB" % (harvester,unicode(harvester.get_stats()),unicode(getattr(usage, "ru_maxrss")/(1024.0))))

