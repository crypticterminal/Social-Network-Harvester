# coding=UTF-8

import sys
import time
import Queue
import threading
import urlparse
import resource

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
    wait_delay = 5 if wait_delay > 5 else wait_delay
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
    elif unicode(fex).startswith("(#613)"):
        msg = u"Exception for the harvester %s for the object %s. Retry:%d. Calls to stream have exceeded the rate of 600 calls per 600 seconds.." % (harvester, 
                                                                                                                unicode(related_object), 
                                                                                                                retry_count)
        sleeper(retry_count)
            
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

def get_feed_paging(page):
    until = None
    new_page = False
    if u"paging" in page and u"next" in page[u"paging"]:
        url = urlparse.parse_qs(page[u"paging"][u"next"])
        until = url[u"until"][0]
        new_page = True
    return ["until",until], new_page

def get_comment_paging(page):
    __after_id = None
    new_page = False
    if u"paging" in page and u"next" in page[u"paging"]:
        url = urlparse.parse_qs(page[u"paging"][u"next"])
        __after_id = url[u"__after_id"][0]
        offset = url[u"offset"][0]
        new_page = True
    return "offset=%s&__after_id%s" % (offset, __after_id), new_page

def update_user_statuses(harvester, statuses):
    for res in statuses:
        status = eval(res.result)
        snhuser = FBUser.objects.get(fid__exact=res.parent)
        try:
            try:
                fb_status = FBPost.objects.get(fid__exact=status["id"])
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
    error = None
    if fbobj:
        error = unicode(fbobj).split(":")[1].strip()
    else:
        msg = u"fobj is None!! bman:%s" % bman
        logger.error(msg)
        
    if error:
        snh_obj = bman["snh_obj"]

        if unicode(error).startswith(u"(#803)"):
            snh_obj.error_triggered = True
            snh_obj.save()
            need_a_break = True
            msg = u"The object does not exists. snh_user:%s" % (unicode(snh_obj))
            logger.error(msg)
        elif unicode(error).startswith("(#613)"):
            msg = u"Exception for the harvester %s. Retry:%s. Calls to stream have exceeded the rate of 600 calls per 600 seconds.." % (harvester, bman["retry"])
            logger.error(msg)            
            sleeper(bman["retry"])

        elif unicode(error).startswith("GraphMethodException"):
            msg = u"GraphMethodException for %s. Error:%s" %(unicode(snh_obj), fanobj)
            logger.error(msg)
            need_a_break = True 
        elif unicode(error).startswith("Unknown path components:"):
            msg = u"Unknown path components for %s. Error:%s" %(unicode(snh_obj), fanobj)
            logger.error(msg)
            need_a_break = True                    

    bman["retry"] += 1
    if bman["retry"] > harvester.max_retry_on_fail:
        msg = u"Max retry for %s. Error:%s" %(bman, fbobj)
        logger.error(msg)
        need_a_break = True                   
    
    return need_a_break

def generic_batch_processor(harvester, bman_list):

    total_retry = 0
    step_size = 40 #Over 20, unknown error will happen...
    next_bman_list = []
    global_retry = 0

    while bman_list:
        waiter = 0
        sleepretry = 0
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.info(u"New batch. Size:%d for %s Mem:%s MB" % (len(bman_list), harvester,unicode(getattr(usage, "ru_maxrss")/(1024.0))))
        split_bman = [bman_list[i:i+step_size] for i  in range(0, len(bman_list), step_size)]

        bman_count = 0
        bman_total = len(split_bman)

        for bman in split_bman:
            retry = 0
            bman_count += 1
            while True:
                try:
                    usage = resource.getrusage(resource.RUSAGE_SELF)
                    logger.info(u"New bman(%d/%d) len:%s InQueue:%d retry:%d total_retry:%d Mem:%s KB" % (bman_count, bman_total, len(bman), len(next_bman_list), retry, total_retry, getattr(usage, "ru_maxrss")/(1024.0)))
                    obj_pos = 0

                    if waiter > 0:
                        logger.info("waiting. %d/30, retry:%d" % (waiter,sleepretry))
                        sleeper(sleepretry)
                        waiter -= 1

                    pyb = [bman[j]["request"] for j in range(0, len(bman))]
                    batch_result = harvester.api_call("batch",{"requests":pyb})
                                
                    for fbobj in batch_result:
                        bman_obj = bman[obj_pos]
                        if type(fbobj) == dict:
                            next = bman_obj["callback"](harvester, bman_obj["snh_obj"], fbobj)
                            if next:
                                next_bman_list += next
                        else:
                            if not manage_error_from_batch(harvester, bman_obj, fbobj):
                                logger.info("Retrying %s" % fbobj)
                                next_bman_list.append(bman_obj)
                                if fbobj:
                                    error = unicode(fbobj).split(":")[1].strip()
                                    if unicode(error).startswith("(#613)"):
                                        waiter += 1
                                        sleepretry += 1
                            else:
                                logger.error("Critical! User will not be retried: %s" % fbobj)
                        obj_pos += 1
                    break
                except FacepyError, fex:
                    (retry, need_a_break) = manage_facebook_exception(retry, harvester, bman, fex)
                    total_retry += 1
                    if need_a_break:
                        logger.error(u"%s %s retry:%d FacepyError:breaking, too many retry!" % (harvester, 
                                                                                                bman, 
                                                                                                retry, 
                                                                                                ))
                        break
                    else:
                        sleeper(retry)
                except:
                    (retry, need_a_break) = manage_exception(retry, harvester, bman)
                    total_retry += 1
                    if need_a_break:
                        logger.error("u%s %s retry:%d Error:breaking, too many retry!" % (harvester, 
                                                                                            bman, 
                                                                                            retry, 
                                                                                            ))
                        break
                    else:
                        sleeper(retry)
        bman_list = next_bman_list
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.debug(u"END bman(%d/%d) len:%s InQueue:%d Mem:%s MB" % (bman_count, bman_total, len(bman), len(next_bman_list), getattr(usage, "ru_maxrss")/(1024.0)))
        next_bman_list = []

def update_user_from_batch(harvester, snhuser, fbuser):
    snhuser.update_from_facebook(fbuser)
    return None

def update_user_batch(harvester):

    all_users = harvester.fbusers_to_harvest.all()
    batch_man = []

    for snhuser in all_users:
        if not snhuser.error_triggered:
            uid = snhuser.fid if snhuser.fid else snhuser.username
            d = {"method": "GET", "relative_url": uid}
            batch_man.append({"snh_obj":snhuser,"retry":0,"request":d, "callback":update_user_from_batch})
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    usage = resource.getrusage(resource.RUSAGE_SELF)
    logger.info(u"Will harvest users for %s Mem:%s MB" % (harvester,unicode(getattr(usage, "ru_maxrss")/(1024.0))))
    generic_batch_processor(harvester, batch_man)

def update_user_status_from_batch(harvester, snhuser, status):

    res = FBResult()
    res.harvester = harvester
    res.result = status
    res.ftype = "FBPost"
    res.fid = status["id"]
    res.parent = snhuser.fid
    res.save()

def update_user_feed_from_batch(harvester, snhuser, fbfeed_page):
    next_bman = []
    feed_count = len(fbfeed_page["data"])
    too_old = False

    if feed_count:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.debug(u"Updating %d feeds: %s Mem:%s MB" % (feed_count, harvester, unicode(getattr(usage, "ru_maxrss")/(1024.0))))

        for feed in fbfeed_page["data"]:
            if feed["created_time"]:
                feed_time = datetime.strptime(feed["created_time"],'%Y-%m-%dT%H:%M:%S+0000')
            else:
                feed_time = datetime.strptime(feed["updated_time"],'%Y-%m-%dT%H:%M:%S+0000')
            
            if feed_time > harvester.harvest_window_from and \
                    feed_time < harvester.harvest_window_to:
                lc_param = ""
                try:
                    latest_comments = FBComment.objects.filter(fid__startswith=feed["id"]).order_by("-created_time")
                    for comment in latest_comments:
                        lc_param = "&__after_id=%s" % comment.fid
                        break
                except ObjectDoesNotExist:
                    pass

                d = {"method": "GET", "relative_url": u"%s" % unicode(feed["id"])}
                next_bman.append({"snh_obj":snhuser, "retry":0, "request":d, "callback":update_user_status_from_batch})

                d = {"method": "GET", "relative_url": u"%s/comments?limit=270%s" % (unicode(feed["id"]), lc_param)}
                next_bman.append({"snh_obj":str(feed["id"]),"retry":0,"request":d, "callback":update_user_comments_from_batch})

                if harvester.update_likes:
                    d = {"method": "GET", "relative_url": u"%s/likes?limit=270%s" % (unicode(feed["id"]), lc_param)}
                    next_bman.append({"snh_obj":str(feed["id"]),"retry":0,"request":d, "callback":update_likes_from_batch})

            if feed_time < harvester.harvest_window_from:
                too_old = True
                break

        paging, new_page = get_feed_paging(fbfeed_page)

        if not too_old and new_page:
            d = {"method": "GET", "relative_url": u"%s/feed?limit=270&%s=%s" % (unicode(snhuser.fid), paging[0], paging[1])}
            next_bman.append({"snh_obj":snhuser, "retry":0, "request":d, "callback":update_user_feed_from_batch})

    return next_bman

def update_user_statuses_batch(harvester):

    all_users = harvester.fbusers_to_harvest.all()
    batch_man = []

    for snhuser in all_users:
        if not snhuser.error_triggered:
            uid = snhuser.fid if snhuser.fid else snhuser.username
            d = {"method": "GET", "relative_url": u"%s/feed?limit=270" % unicode(uid)}
            batch_man.append({"snh_obj":snhuser,"retry":0,"request":d,"callback":update_user_feed_from_batch})
        else:
            logger.info(u"Skipping status update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    usage = resource.getrusage(resource.RUSAGE_SELF)
    logger.info(u"Will harvest statuses for %s Mem:%s MB" % (harvester,unicode(getattr(usage, "ru_maxrss")/(1024.0))))
    generic_batch_processor(harvester, batch_man)

def update_user_comments(harvester, fbcomments):
    for fbresult in fbcomments:
        fbcomment = eval(fbresult.result)
        status = FBPost.objects.get(fid__exact=fbresult.parent)
        try:
            try:
                snh_comment = FBComment.objects.get(fid__exact=fbcomment["id"])
            except ObjectDoesNotExist:
                snh_comment = FBComment()
                snh_comment.save()
            snh_comment.update_from_facebook(fbcomment, status)                
        except:
            msg = u"Cannot update comment %s" % (fbcomment)
            logger.exception(msg) 

def update_user_comments_from_batch(harvester, statusid, fbcomments_page):
    next_bman = []
    comment_count = len(fbcomments_page["data"])

    if comment_count:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.debug(u"Updating %d comments: %s Mem:%s MB" % (comment_count, harvester, unicode(getattr(usage, "ru_maxrss")/(1024.0))))

        for comment in fbcomments_page["data"]:
            res = FBResult()
            res.harvester = harvester
            res.result = comment
            res.ftype = "FBComment"
            res.fid = comment["id"]
            res.parent = statusid
            res.save()

        paging, new_page = get_comment_paging(fbcomments_page)

        if new_page:
            d = {"method": "GET", "relative_url": u"%s/comments?limit=270&%s" % (statusid, paging)}
            next_bman.append({"snh_obj":statusid,"retry":0,"request":d,"callback":update_user_comments_from_batch})
        
    return next_bman

def update_likes_from_batch(harvester, statusid, fblikes_page):
    next_bman = []
    likes_count = len(fblikes_page["data"])

    if likes_count:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.debug(u"Updating %d likes: %s statusid:%s Mem:%s MB" % (likes_count, statusid, harvester, unicode(getattr(usage, "ru_maxrss")/(1024.0))))

        res = FBResult()
        res.harvester = harvester
        res.result = fblikes_page["data"]
        res.ftype = "FBPost.likes"
        res.fid = statusid
        res.parent = statusid
        res.save()

        paging, new_page = get_comment_paging(fblikes_page)
        
        if new_page:
            d = {"method": "GET", "relative_url": u"%s/likes?limit=270&%s" % (statusid, paging)}
            next_bman.append({"snh_obj":statusid,"retry":0,"request":d,"callback":update_likes_from_batch})

    return next_bman

queue = Queue.Queue()

class ThreadStatus(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        statuscount = 0
        logger.info(u"ThreadStatus %s. Start." % self)
        while True: 
            try:
                fid = self.queue.get()

                user = FBUser.objects.filter(fid__exact=fid)[0]
                results = FBResult.objects.filter(parent__exact=user.fid).filter(ftype__exact="FBPost")
                logger.info(u"ThreadStatus. Beginning user %s. %s" % (user, user.fid))
                for elem in results:
                    self.update_user_status(eval(elem.result),user)
                    statuscount += 1
                logger.debug(u"ThreadStatus %s in progress. Current status count %d" % (self, statuscount))


                #signals to queue job is done
            except Queue.Empty:
                logger.info(u"ThreadStatus %s. Queue is empty." % self)
                break;
            except:
                msg = u"ThreadStatus %s. Error" % self
                logger.exception(msg)
            finally:
                self.queue.task_done()
                
        logger.info(u"ThreadStatus %s. End." % self)

    def update_user_status(self, fbstatus, user):
        try:
            try:
                snh_status = FBPost.objects.get(fid__exact=fbstatus["id"])
            except ObjectDoesNotExist:
                snh_status = FBPost(user=user)
                snh_status.save()
            snh_status.update_from_facebook(fbstatus,user)
            likes_list = FBResult.objects.filter(fid__startswith=fbstatus["id"]).filter(ftype__exact="FBPost.likes")
            for likes in likes_list:
                snh_status.update_likes_from_facebook(eval(likes.result))
        except:
            msg = u"Cannot update status %s for %s" % (unicode(fbstatus), user.fid if user.fid else "0")
            logger.exception(msg) 

class ThreadComment(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        count = 0
        commentcount = 0
        logger.info(u"ThreadComment %s. Start." % self)
        while True: 

            try:
                fid = self.queue.get()
                if fid:
                    post = FBPost.objects.get(fid__exact=fid)
                    results = FBResult.objects.filter(parent__exact=post.fid).filter(ftype__exact="FBComment")
                    for elem in results:
                        self.update_comment_status(eval(elem.result), post)
                        commentcount += 1
                    logger.debug(u"ThreadComment %s in progress. Current comment count %d" % (self, commentcount))
                    
                else:
                    logger.error(u"ThreadComment %s. fid is none! %s." % (self, fid))
                #signals to queue job is done
            except Queue.Empty:
                logger.info(u"ThreadComment %s. Queue is empty." % self)
                break;
            except:
                msg = u"ThreadComment %s. Error." % self
                logger.exception(msg)                 
            finally:
                self.queue.task_done()
                count += 1
                if count == 1000:
                    count = 0
                    logger.info("ThreadComment %s. Element to go: %d" % (self,queue.qsize()))
                
        logger.info(u"ThreadComment %s. End." % self)

    def update_comment_status(self, comment, post):
        try:
            try:
                fbcomment = FBComment.objects.get(fid__exact=comment["id"])
            except ObjectDoesNotExist:
                fbcomment = FBComment(post=post)
                fbcomment.save()
            fbcomment.update_from_facebook(comment,post)
        except:
            msg = u"Cannot update comment %s for %s" % (unicode(comment), post.fid if post.fid else "0")
            logger.exception(msg) 


def compute_new_post(harvester):
    global queue
    queue = Queue.Queue()
    all_users = harvester.fbusers_to_harvest.values("fid")
    for user in all_users:
        queue.put(user["fid"])

    for i in range(4):
        t = ThreadStatus(queue)
        t.setDaemon(True)
        t.start()
      
    queue.join()

def compute_new_comment(harvester):
    global queue
    queue = Queue.Queue()

    all_comments =  FBResult.objects.filter(ftype__exact="FBComment").values("parent")
    for comment in all_comments:
        queue.put(comment["parent"])

    for i in range(4):
        t = ThreadComment(queue)
        t.setDaemon(True)
        t.start()
      
    queue.join()

def run_harvester_v3(harvester):
    harvester.start_new_harvest()
    try:
        update_user_batch(harvester)
        update_user_statuses_batch(harvester)
        start = time.time()
        logger.info(u"Starting results computation")
        compute_new_post(harvester) 
        compute_new_comment(harvester)
        FBResult.objects.filter(harvester=harvester).delete()
        logger.info(u"Results computation complete in %ss" % (time.time() - start))

    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s Mem:%s MB" % (harvester,unicode(harvester.get_stats()),unicode(getattr(usage, "ru_maxrss")/(1024.0))))

