# coding=UTF-8

import twitter
import time
import datetime

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

def get_latest_statuses_page(harvester, user, page):
    latest_statuses_page = harvester.api_call("GetUserTimeline",
                                                {
                                                u"screen_name":unicode(user.screen_name), 
                                                u"since_id":None, 
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
    msg = u"Exception for the harvester %s for the user %s(%d) at page %d. Retry:%d" % (harvester, unicode(user), user.fid if user.fid else 0, page, retry_count)
    logger.exception(msg)
    retry_count += 1
    return (retry_count, retry_count > harvester.max_retry_on_fail)

def manage_twitter_exception(retry_count, harvester, user, page, tex):
    retry_count += 1

    if unicode(tex) == u"Not found":
        user.error_triggered = True
        user.save()
        need_a_break = True
        msg = u"Exception for the harvester %s for the user %s(%d) at page %d. Retry:%d. The user does not exists!" % (harvester, unicode(user), user.fid if user.fid else 0, page, retry_count)
        logger.exception(msg)
    elif unicode(tex) == u"Capacity Error":
        logger.debug(u"%s:%s(%d):%d. Capacity Error. Retrying." % (harvester, unicode(user), user.fid if user.fid else 0, page))
    elif unicode(tex).startswith(u"Rate limit exceeded"):
        harvester.update_client_stats()
        msg = u"Exception for the harvester %s for the user %s(%d) at page %d. Retry:%d." % (harvester, unicode(user), user.fid if user.fid else 0, page, retry_count)
        logger.exception(msg)
        raise
    else:
        msg = u"Exception for the harvester %s for the user %s(%d) at page %d. Retry:%d." % (harvester, unicode(user), user.fid if user.fid else 0, page, retry_count)
        logger.exception(msg)

    return (retry_count, retry_count > harvester.max_retry_on_fail)

def get_timedelta(twitter_time):
    ts = datetime.strptime(twitter_time,'%a %b %d %H:%M:%S +0000 %Y')
    return (datetime.utcnow() - ts).days


def get_latest_statuses(harvester, user):

    page = 1
    retry = 0
    lsp = []
    latest_statuses = []

    while True:
        try:
            logger.debug(u"%s:%s(%d):%d" % (harvester, unicode(user), user.fid if user.fid else 0, page))
            lsp = get_latest_statuses_page(harvester, user, page)
            
            if lsp:
                latest_statuses += lsp
            else:
                break

            if get_timedelta(lsp[len(lsp)-1].created_at) >= harvester.dont_harvest_further_than:
                logger.debug(u"%s:%s(%d). max date reached. Now:%s, Status.created_at:%s, Delta:%s" % 
                                                                (harvester, 
                                                                unicode(user), 
                                                                user.fid if user.fid else 0, 
                                                                datetime.utcnow(), 
                                                                datetime.strptime(lsp[len(lsp)-1].created_at,'%a %b %d %H:%M:%S +0000 %Y'), 
                                                                get_timedelta(lsp[len(lsp)-1].created_at)
                                                                ))
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

def update_user_statuses(statuses, user):
        for status in statuses:
            try:
                try:
                    tw_status = TWStatus.objects.get(fid__exact=status.id)
                except ObjectDoesNotExist:
                    tw_status = TWStatus(user=user)
                    tw_status.save()
                tw_status.update_from_twitter(status,user)
            except:
                msg = u"Cannot update status %s for %s:(%d)" % (unicode(status), unicode(user), user.fid if user.fid else 0)
                logger.exception(msg) 

def run_harvester_v2(harvester):

    harvester.start_new_harvest()
    user = harvester.get_next_user_to_harvest()
    logger.info(u"START: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
    try:
        while user and harvester.remaining_hits > 0:
            if not user.error_triggered:
                logger.info(u"Start: %s:%s(%d). Hits to go: %d" % (harvester, unicode(user), user.fid if user.fid else 0, harvester.remaining_hits))
                ls = get_latest_statuses(harvester, user)
                update_user(ls, user)
                update_user_statuses(ls, user)
            else:
                logger.info(u"Skipping: %s:%s(%d) because user has triggered the error flag." % (harvester, unicode(user), user.fid if user.fid else 0))
            user = harvester.get_next_user_to_harvest()
    except twitter.TwitterError:
        harvester.update_client_stats()
        pass
    finally:
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s" % (harvester,unicode(harvester.get_stats())))
    

