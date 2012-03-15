# coding=UTF-8

import sys
import time
import urlparse
import resource
import json
import inspect
import traceback

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
    retry_delay = 1
    wait_delay = retry_count*retry_delay
    wait_delay = 60 if wait_delay > 60 else wait_delay
    time.sleep(wait_delay)

def manage_exception(retry_count, harvester, related_object):
    msg = u"Exception for the harvester %s for the object %s(%s). Retry:%d" % (harvester, 
                                                                                unicode(related_object), 
                                                                                related_object.fid if related_object.fid else "0", 
                                                                                retry_count)
    logger.exception(msg)
    retry_count += 1
    return (retry_count, retry_count > harvester.max_retry_on_fail)

def manage_facebook_exception(retry_count, harvester, related_object, fex):
    retry_count += 1

    if unicode(fex).startswith(u"(#803)"):
        user.error_triggered = True
        user.save()
        msg = u"Exception for the harvester %s for the object %s(%s). Retry:%d. The user does not exists!" % (harvester, 
                                                                                                                unicode(related_object), 
                                                                                                                related_object.fid if related_object.fid else "0", 
                                                                                                                retry_count)
        logger.exception(msg)
        need_a_break = True
    elif unicode(fex).startswith("Unknown path components:"):
        msg = u"Exception for the harvester %s for the object %s(%s). Retry:%d. The user does not exists!" % (harvester, 
                                                                                                                unicode(related_object), 
                                                                                                                related_object.fid if related_object.fid else "0",
                                                                                                                retry_count)
        logger.exception(msg)
        need_a_break = True                    
    else:
        msg = u"Exception for the harvester %s for the object %s(%s). Retry:%d. The user does not exists!" % (harvester, 
                                                                                                                unicode(related_object), 
                                                                                                                related_object.fid if related_object.fid else "0", 
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
        limit = url[u"limit"][0]
        new_page = True
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

def get_facebook_list(harvester, url, related_object, page_func, history_limit=True):
    complete_list = []
    page = 0
    retry = 0
    until = ["until",None]
    limit = 6000
    while True:
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            logger.info(u"%s %s page:%d retry:%d Mem:%s KB" % (harvester, related_object, page, retry, unicode(getattr(usage, "ru_maxrss")/(1024.0))))
            latest_page = harvester.api_call("get",{"path":url,until[0]:until[1],"limit":limit})
            delta = 0
            last_post_time = ""
            max_age_reached = False

            if "data" in latest_page and latest_page["data"]:
                logger.debug(u"%s %s page:%d retry:%d adding: %d objects" % (harvester, 
                                                                                        related_object, 
                                                                                        page, 
                                                                                        retry, 
                                                                                        len(latest_page["data"])))
                for data in latest_page["data"]:
                    last_post_time = data["created_time"]
                    delta = get_timedelta(last_post_time)
                    if delta >= harvester.dont_harvest_further_than:
                        max_age_reached = True
                    else:
                        complete_list.append(data)
                
            else:
                logger.debug(u"%s %s page:%d retry:%d No more data?" % (harvester, 
                                                                                    related_object, 
                                                                                    page, 
                                                                                    retry, 
                                                                                    ))
                break

            if max_age_reached:
                logger.debug(u"%s %s page:%d retry:%d Max age reached. now:%s then:%s delta:%s" % (harvester, 
                                                                                    related_object, 
                                                                                    page, 
                                                                                    retry, 
                                                                                    datetime.utcnow(),
                                                                                    last_post_time,
                                                                                    delta,
                                                                                    ))
                break

            until, new_page = page_func(latest_page)
            if not new_page:
                logger.debug(u"%s %s page:%d retry:%d No new page?" % (harvester, 
                                                                                    related_object, 
                                                                                    page, 
                                                                                    retry, 
                                                                                    ))
                break

            retry = 0
            page += 1
            latest_page = None

        except FacepyError, fex:
            (retry, need_a_break) = manage_facebook_exception(retry, harvester, related_object, fex)
            if need_a_break:
                logger.debug(u"%s %s page:%d retry:%d FacepyError:breaking, too many retry!" % (harvester, 
                                                                                                            related_object, 
                                                                                                            page, 
                                                                                                            retry, 
                                                                                                ))
                break
            else:
                sleeper(retry)
        except:
            (retry, need_a_break) = manage_exception(retry, harvester, related_object)
            if need_a_break:
                logger.debug("u%s %s page:%d retry:%d Error:breaking, too many retry!" % (harvester, 
                                                                                                    related_object, 
                                                                                                    page, 
                                                                                                    retry, 
                                                                                            ))
                break
            else:
                sleeper(retry)
    return complete_list

def get_latest_statuses(harvester, user):

    urlid = user.fid if user.fid else user.username
    url = u"%s/feed" % urlid
    usage = resource.getrusage(resource.RUSAGE_SELF)
    logger.debug(u"%s %s %s Will get statuses. Mem:%sKB" % (harvester, user, url,unicode(getattr(usage, "ru_maxrss")/(1024.0))))
    latest_statuses = get_facebook_list(harvester, url, user, get_status_paging)
    return latest_statuses

def get_user(harvester, user):

    urlid = user.fid if user.fid else user.username
    url = u"%s" % urlid
    logger.debug(u"%s %s %s Will get user" % (harvester, user, url))
    fbuser = None
    retry = 0

    while True:
        try:
            fbuser = harvester.api_call("get",{"path":url})
            break
        except FacepyError, fex:
            (retry, need_a_break) = manage_facebook_exception(retry, harvester, user, fex)
            if need_a_break:
                logger.debug(u"%s %s retry:%d FacepyError:breaking, too many retry!" % (harvester, 
                                                                                        user, 
                                                                                        retry, 
                                                                                        ))
                break
            else:
                sleeper(retry)   
        except:
            (retry, need_a_break) = manage_exception(retry, harvester, user)
            if need_a_break:
                logger.debug("u%s %s retry:%d Error:breaking, too many retry!" % (harvester, 
                                                                                    user, 
                                                                                    retry, 
                                                                                    ))
                break
            else:
                sleeper(retry)
    return fbuser

def get_comments(harvester, status, user, count, total):

    latest_comments = []
    url = u"%s/comments" % status.fid
    usage = resource.getrusage(resource.RUSAGE_SELF)
    logger.debug(u"%s %s %s Will get comment. Mem:%s KB" % (harvester, user, url,unicode(getattr(usage, "ru_maxrss")/(1024.0))))
    latest_comments = get_facebook_list(harvester, url, status, get_comment_paging)
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
                #if fb_status.comments_count > 0:
                #    update_comment(harvester, fb_status, user, status_count, total_status)
                    
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
        usage = resource.getrusage(resource.RUSAGE_SELF)
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s Mem:%s KB" % (harvester,unicode(harvester.get_stats()),unicode(getattr(usage, "ru_maxrss")/(1024.0))))

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

def update_user_from_batch(snhuser, fbuser):
    snhuser.update_from_facebook(fbuser)

def manage_error_from_batch(harvester, batch_man_obj, fbobj):

    need_a_break = False
    error = unicode(fbobj).split(":")[1].strip()
    snh_obj = batch_man_obj["snh_obj"]

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

    batch_man_obj["retry"] += 1
    if batch_man_obj["retry"] > harvester.max_retry_on_fail:
        msg = u"Max retry for %s. Error:%s" %(unicode(snh_obj), fbobj)
        logger.error(msg)
        need_a_break = True                   
    
    return need_a_break

def update_user_batch(harvester):

    all_users = harvester.fbusers_to_harvest.all()
    step_size = 2
    batch_man = []
    retry_obj = []

    for snhuser in all_users:
        if not snhuser.error_triggered:
            uid = snhuser.fid if snhuser.fid else snhuser.username
            d = {"method": "GET", "relative_url": u"%s" % unicode(uid)}
            batch_man.append({"snh_obj":snhuser,"retry":0,"request":d})
        else:
            logger.info(u"Skipping: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    while batch_man:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.info(u"New batch: %s Mem:%s KB" % (harvester,unicode(getattr(usage, "ru_maxrss")/(1024.0))))

        split_bman = [batch_man[i:i+step_size] for i  in range(0, len(batch_man), step_size)]
        for bman in split_bman:
            pyb = [bman[j]["request"] for j in range(0, len(bman))]
            batch_result = harvester.api_call("batch",{"batch":json.dumps(pyb)})
            obj_pos = 0
            for fbobj in batch_result:
                bman_obj = bman[obj_pos]
                if type(fbobj) == type(dict()):
                    update_user_from_batch(bman_obj["snh_obj"], fbobj)
                else:
                    if not manage_error_from_batch(harvester, bman_obj, fbobj):
                        retry_obj.append(bman_obj)
                obj_pos += 1

        batch_man = retry_obj
        retry_obj = []
        print "will retry:", batch_man
        #if retry_obj:
        #    msg = u"There are users to retry, but retry is not implemented!!! %s" %(unicode(retry_obj))
        #    logger.error(msg)
        

def update_user_statuses_batch(harvester):
    
    pass


def run_harvester_v3(harvester):
    harvester.start_new_harvest()
    try:
        update_user_batch(harvester)
        update_user_statuses_batch(harvester)
    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s Mem:%s KB" % (harvester,unicode(harvester.get_stats()),unicode(getattr(usage, "ru_maxrss")/(1024.0))))

