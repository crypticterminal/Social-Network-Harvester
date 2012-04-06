# coding=UTF-8

import twitter
import time
import datetime

from twython.twython import TwythonError, TwythonAPILimit, TwythonAuthError, TwythonRateLimitError

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from snh.models.twittermodel import *

import snhlogger
logger = snhlogger.init_logger(__name__, "twitter.log")

def run_twitter_harvester():
    harvester_list = TwitterHarvester.objects.all()

    for harvester in harvester_list:
        harvester.update_client_stats()
        logger.info(u"The harvester %s is %s" % 
                                                (unicode(harvester), 
                                                "active" if harvester.is_active else "inactive"))
        if harvester.is_active and not harvester.remaining_hits > 0:
            logger.warning(u"The harvester %s is %s but has exceeded the rate limit. Need to wait? %s" % 
                                                (unicode(harvester), 
                                                "active" if harvester.is_active else "inactive", 
                                                harvester.get_stats()))

        if harvester.is_active and harvester.remaining_hits > 0:
            run_harvester_v2(harvester)

        if harvester.is_active:        
            run_harvester_search(harvester)

def get_latest_statuses_page(harvester, user, page):

    since_max = [u"since_id",None]
    if user.was_aborted:
        since_max = [u"max_id",user.last_harvested_status.fid]
        
    latest_statuses_page = harvester.api_call("GetUserTimeline",
                                                {
                                                u"screen_name":unicode(user.screen_name), 
                                                since_max[0]:since_max[1], 
                                                u"include_rts":True, 
                                                u"include_entities":True,
                                                u"count":200,
                                                u"page":page,
                                                })
    return latest_statuses_page

def sleeper(retry_count):
    retry_delay = 1
    wait_delay = retry_count*retry_delay
    wait_delay = 60 if wait_delay > 60 else wait_delay
    time.sleep(wait_delay)

def manage_exception(retry_count, harvester, user, page):
    msg = u"Exception for the harvester %s for %s at page %d. Retry:%d" % (harvester, unicode(user), page, retry_count)
    logger.exception(msg)
    retry_count += 1
    return (retry_count, retry_count > harvester.max_retry_on_fail)

def manage_twitter_exception(retry_count, harvester, user, page, tex):
    retry_count += 1

    if unicode(tex) == u"Not found":
        user.error_triggered = True
        user.save()
        need_a_break = True
        msg = u"Exception for the harvester %s for %s at page %d. Retry:%d. The user does not exists!" % (harvester, unicode(user), page, retry_count)
        logger.exception(msg)
    elif unicode(tex) == u"Capacity Error":
        logger.debug(u"%s:%s:%d. Capacity Error. Retrying." % (harvester, unicode(user), page))
    elif unicode(tex).startswith(u"Rate limit exceeded"):
        harvester.update_client_stats()
        msg = u"Exception for the harvester %s for %s at page %d. Retry:%d." % (harvester, unicode(user), page, retry_count)
        logger.exception(msg)
        raise
    else:
        print tex.__dict__
        msg = u"Exception for the harvester %s for %s at page %d. Retry:%d. %s" % (harvester, unicode(user), page, retry_count, tex)
        logger.exception(msg)

    return (retry_count, retry_count > harvester.max_retry_on_fail)

def get_latest_statuses(harvester, user):

    page = 1
    retry = 0
    lsp = []
    latest_statuses = []
    too_old = False

    while not too_old:
        try:
            logger.debug(u"%s:%s(%d):%d" % (harvester, unicode(user), user.fid if user.fid else 0, page))
            lsp = get_latest_statuses_page(harvester, user, page)
            if len(lsp) != 0:
                for status in lsp:
                    status_time = datetime.strptime(status.created_at,'%a %b %d %H:%M:%S +0000 %Y')
                    if status_time > harvester.harvest_window_from and \
                            status_time < harvester.harvest_window_to:
                        update_user_status(status, user)

                    if status_time < harvester.harvest_window_from:
                        too_old = True
                        break
            else:
                break
            page = page + 1
            retry = 0
        except twitter.TwitterError, tex:
            (retry, need_a_break) = manage_twitter_exception(retry, harvester, user, page, tex)
            if need_a_break:
                break
            else:
                sleeper(retry)             
        except:
            (retry, need_a_break) = manage_exception(retry, harvester, user, page)
            if need_a_break:
                break
            else:
                sleeper(retry) 

    return latest_statuses

def update_user(statuses, user):
        try:
            if statuses:
                user.update_from_twitter(statuses[0].user)
            else:
                raise Exception("Cannot update user (%s) without a status!" % unicode(user))
        except:
            msg = u"Cannot update user info for %s:(%d)" % (unicode(user), user.fid if user.fid else 0)
            logger.exception(msg)    

def update_user_status(status, user):
    try:
        try:
            tw_status = TWStatus.objects.get(fid__exact=status.id)
        except ObjectDoesNotExist:
            tw_status = TWStatus(user=user)
            tw_status.save()
        tw_status.update_from_twitter(status,user)
        user.last_harvested_status = tw_status
        user.save()
    except:
        msg = u"Cannot update status %s for %s:(%d)" % (unicode(status), unicode(user), user.fid if user.fid else 0)
        logger.exception(msg) 

def update_user_statuses(statuses, user):
    for status in statuses:
        update_user_status(status, user)

def user_from_search(harvester, twuser):
    snh_user = None
    try:
        snh_user = TWUser.objects.get(Q(fid__exact=twuser["id"])|Q(screen_name__exact=twuser["screen_name"]))
    except ObjectDoesNotExist:
        snh_user = TWUser(
                            fid=twuser["id"],
                            screen_name=twuser["screen_name"],
                            )
        snh_user.save()   

    return snh_user

def status_from_search(harvester, tw_status):
    user = None
    snh_status = None
    try:
        try:
            user = TWUser.objects.get(Q(fid__exact=tw_status["from_user_id"])|Q(screen_name__exact=tw_status["from_user"]))
        except ObjectDoesNotExist:
            user = TWUser(
                            fid=tw_status["from_user_id"],
                            screen_name=tw_status["from_user"],
                         )
            user.save()

        try:
            snh_status = TWStatus.objects.get(fid__exact=tw_status["id"])
        except ObjectDoesNotExist:
            snh_status = TWStatus(
                                    fid=tw_status["id"],
                                    user=user,
                                    )
            snh_status.save()
        snh_status.update_from_rawtwitter(tw_status, user)
    except:
        msg = u"Cannot update status %s for user %s)" % (unicode(tw_status), unicode(user))
        logger.exception(msg) 

    return snh_status

def update_search(snh_search, snh_status):

    if snh_search.status_list.filter(fid__exact=snh_status.fid).count() == 0:
        snh_search.status_list.add(snh_status)
        snh_search.save()

def call_search(harvester, term, page):
    retry = 0
    status_list = None
    next_page = True
    while status_list is None:
        try:
            params = {   "parameters":{
                                        u"q":term, 
                                        #since_max[0]:since_max[1], 
                                        u"rpp":"100",
                                        u"page":"%d" % page,
                                        u"include_rts":"true", 
                                        u"include_entities":"true",
                                    }
                                }
            logger.info(u"Getting new page:%d retry:%d, params:%s" % (page,retry,params))
            data = harvester.api_call("GetPlainSearch", params)
            if "results" in data:
                status_list = data["results"]
            if "next_page" in data:
                print data["next_page"], page
            else:
                next_page = False
                print "No next page!", term, page

        except twitter.TwitterError, tex:
            (retry, need_a_break) = manage_twitter_exception(retry, harvester, term, page, tex)
            if need_a_break:
                break
            else:
                sleeper(retry)

    logger.info(u"Next page for %s: %s Hits to go: %d, len:%d" % (term, harvester, harvester.remaining_hits,len(status_list)))
    return status_list, next_page

def search_term(harvester, twsearch):
    page = 1
    too_old = False
    status_list, next_page = call_search(harvester, twsearch.term, page)
    while status_list and not too_old:
        page += 1
        for status in status_list:

            status_time = datetime.strptime(status["created_at"],'%a, %d %b %Y %H:%M:%S +0000')
            if status_time > harvester.harvest_window_from and \
                    status_time < harvester.harvest_window_to:

                snh_status = status_from_search(harvester, status)
                update_search(twsearch, snh_status)

            if status_time < harvester.harvest_window_from or not next_page:
                too_old = True
                break
        logger.info(u"last status date: %s" % status_time)
        if next_page:
            status_list, next_page = call_search(harvester, twsearch.term, page)

def update_user_twython(twuser, user):
        try:
            user.update_from_rawtwitter(twuser,twython=True)
        except:
            msg = u"Cannot update user info for %s:(%d)" % (unicode(twuser), user.fid if user.fid else 0)
            logger.exception(msg)    

def update_users_twython(harvester):
    all_users = harvester.twusers_to_harvest.all()
    screen_names = []
    user_screen_name = {}

    for user in all_users:
        screen_names.append(user.screen_name)
        user_screen_name[user.screen_name.upper()] = user

    step_size = 100
    split_screen_names = [screen_names[i:i+step_size] for i  in range(0, len(screen_names), step_size)]

    for screen_names in split_screen_names:
        tt = harvester.get_tt_client()
        twuser_list_page = tt.bulkUserLookup(screen_names=screen_names, include_entities="true")
        logger.info(u"Twython hit to go: %d" % (tt.getRateLimitStatus()["remaining_hits"]))
        for twuser in twuser_list_page:
            screen_name = twuser["screen_name"].upper()
            user = user_screen_name[screen_name]
            update_user_twython(twuser, user)

def run_harvester_v2(harvester):

    harvester.start_new_harvest()
    logger.info(u"START: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
    try:
        if True:
            update_users_twython(harvester)

        if True:
            user = harvester.get_next_user_to_harvest()
            while user and harvester.remaining_hits > 0:
                if not user.error_triggered:
                    logger.info(u"Start: %s:%s(%d). Hits to go: %d" % (harvester, unicode(user), user.fid if user.fid else 0, harvester.remaining_hits))
                    get_latest_statuses(harvester, user)
                else:
                    logger.info(u"Skipping: %s:%s(%d) because user has triggered the error flag." % (harvester, unicode(user), user.fid if user.fid else 0))

                user.was_aborted = False
                user.save()
                user = harvester.get_next_user_to_harvest()

    except twitter.TwitterError:
        harvester.update_client_stats()
    finally:
        harvester.end_current_harvest()
        if harvester.last_user_harvest_was_aborted:
            aborted_user = harvester.get_current_harvested_user()
            aborted_user.was_aborted = True
            aborted_user.save()

def run_harvester_search(harvester):
            
    if True:
        logger.info(u"START SEARCH API: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
        try:
            all_twsearch = harvester.twsearch_to_harvest.all()
            for twsearch in all_twsearch:
                search_term(harvester, twsearch)
        except twitter.TwitterError, e:
            msg = u"ERROR for %s" % twsearch.term
            logger.exception(msg)    
        finally:
            logger.info(u"End REST API: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
        
    logger.info(u"End: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))


