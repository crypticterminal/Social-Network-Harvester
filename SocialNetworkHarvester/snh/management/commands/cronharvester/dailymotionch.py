# coding=UTF-8

from datetime import timedelta
import resource
import time

from django.core.exceptions import ObjectDoesNotExist
from snh.models.dailymotionmodel import *

import snhlogger
logger = snhlogger.init_logger(__name__, "dailymotion.log")

def run_dailymotion_harvester():
    harvester_list = DailyMotionHarvester.objects.all()
    for harvester in harvester_list:
        logger.info(u"The harvester %s is %s" % 
                                                (unicode(harvester), 
                                                "active" if harvester.is_active else "inactive"))
        if harvester.is_active:
            run_harvester_v1(harvester)

def sleeper(retry_count):
    retry_delay = 1
    wait_delay = retry_count*retry_delay
    wait_delay = 10 if wait_delay > 10 else wait_delay
    time.sleep(wait_delay)

def get_timedelta(dm_time):
    ts = datetime.strptime(dm_time,'%Y-%m-%dT%H:%M:%S+0000')
    return (datetime.utcnow() - ts).days

def get_comment_paging(page):
    __after_id = None
    new_page = False
    if u"paging" in page and u"next" in page[u"paging"]:
        url = urlparse.parse_qs(page[u"paging"][u"next"])
        __after_id = url[u"__after_id"][0]
        new_page = True
    return ["__after_id",__after_id], new_page

def update_users(harvester):

    all_users = harvester.dmusers_to_harvest.all()

    for snhuser in all_users:
        if not snhuser.error_triggered:
            result = harvester.api_call("GET",
                                        str(
                                            "/user/%(username)s?fields="
                                            "id,"
                                            "type,"
                                            "status,"
                                            "username,"
                                            "screenname,"
                                            #"fullname," #access_required
                                            "created_time,"
                                            "description,"
                                            "language,"
                                            "gender,"
                                            #"email," #access_required
                                            #"birthday," #access_required
                                            #"ip," #access_required
                                            #"useragent," #access_required
                                            "views_total,"
                                            "videos_total,"
                                            #"cloudkey," #access_required
                                            "url,"
                                            "avatar_small_url,"
                                            "avatar_medium_url,"
                                            "avatar_large_url,"
                                            "tile,"
                                            "tile.id,"
                                            "tile.video,"
                                            "tile.type,"
                                            "tile.title,"
                                            "tile.summary,"
                                            "tile.mode,"
                                            "tile.icon_url,"
                                            "tile.icon2x_url,"
                                            "tile.thumbnail_url,"
                                            "tile.thumbnail2x_url,"
                                            "tile.views_total,"
                                            "tile.videos_total,"
                                            "tile.context,"
                                            "tile.explicit,"
                                            "tile.sorts,"
                                            "tile.sorts_labels,"
                                            "tile.sorts_default,"
                                            "tile.filters,"
                                            "tile.filters_labels,"
                                            "tile.filters_default,"
                                            "tile.new_items,"
                                            "videostar,"
                                            "videostar.id,"
                                            "videostar.title,"
                                            "videostar.tags,"
                                            "videostar.tag,"
                                            "videostar.channel,"
                                            "videostar.description,"
                                            "videostar.language,"
                                            "videostar.country,"
                                            "videostar.url,"
                                            "videostar.tiny_url,"
                                            "videostar.created_time,"
                                            "videostar.modified_time,"
                                            "videostar.taken_time,"
                                            "videostar.status,"
                                            "videostar.encoding_progress,"
                                            "videostar.type,"
                                            "videostar.paywall,"
                                            "videostar.rental_price,"
                                            "videostar.rental_price_formatted,"
                                            "videostar.rental_duration,"
                                            "videostar.mode,"
                                            "videostar.onair,"
                                            "videostar.live_publish_url,"
                                            #"videostar.audience_url," #access_required
                                            #"videostar.ads," #access_required
                                            "videostar.private,"
                                            "videostar.explicit,"
                                            "videostar.published,"
                                            "videostar.duration,"
                                            "videostar.allow_comments,"
                                            "videostar.owner,"
                                            "videostar.user,"
                                            "videostar.owner_screenname,"
                                            "videostar.owner_username,"
                                            "videostar.owner_fullname,"
                                            "videostar.owner_url,"
                                            "videostar.owner_avatar_small_url,"
                                            "videostar.owner_avatar_medium_url,"
                                            "videostar.owner_avatar_large_url,"
                                            "videostar.thumbnail_url,"
                                            "videostar.thumbnail_small_url,"
                                            "videostar.thumbnail_medium_url,"
                                            "videostar.thumbnail_large_url,"
                                            "videostar.rating,"
                                            "videostar.ratings_total,"
                                            "videostar.views_total,"
                                            "videostar.views_last_hour,"
                                            "videostar.views_last_day,"
                                            "videostar.views_last_week,"
                                            "videostar.views_last_month,"
                                            "videostar.comments_total,"
                                            "videostar.bookmarks_total,"
                                            "videostar.embed_html,"
                                            "videostar.embed_url,"
                                            "videostar.swf_url,"
                                            "videostar.aspect_ratio,"
                                            #"videostar.log_view_url," #access_required
                                            #"videostar.log_external_view_url," #access_required
                                            #"videostar.log_view_urls," #access_required
                                            #"videostar.log_external_view_urls," #access_required
                                            "videostar.upc,"
                                            "videostar.isrc,"
                                            #"videostar.stream_h264_ld_url," #access_required
                                            #"videostar.stream_3gp_url," #access_required
                                            #"videostar.stream_h264_url," #access_required
                                            #"videostar.stream_h264_hq_url," #access_required
                                            #"videostar.stream_h264_hd_url," #access_required
                                            #"videostar.stream_h264_hd1080_url," #access_required
                                            #"videostar.stream_h264_ld_rtmpe_url," #access_required
                                            #"videostar.stream_3gp_rtmpe_url," #access_required
                                            #"videostar.stream_h264_rtmpe_url," #access_required
                                            #"videostar.stream_h264_hq_rtmpe_url," #access_required
                                            #"videostar.stream_h264_hd_rtmpe_url," #access_required
                                            #"videostar.stream_h264_hd1080_rtmpe_url," #access_required
                                            #"videostar.stream_live_hls_url," #access_required
                                            #"videostar.stream_live_rtmp_url," #access_required
                                            #"videostar.stream_live_rtsp_url," #access_required
                                            #"videostar.publish_date," #access_required
                                            #"videostar.expiry_date," #access_required
                                            "videostar.geoblocking,"
                                            "videostar.3d" %
                                            {
                                                "username":snhuser.username,
                                            })
                                        )
            logger.debug(u"rez: %s", result["result"]["username"])
            snhuser.update_from_dailymotion(result["result"])
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    usage = resource.getrusage(resource.RUSAGE_SELF)
    logger.info(u"Will harvest users for %s Mem:%s MB" % (harvester,unicode(getattr(usage, "ru_maxrss")/(1024.0))))


def run_harvester_v1(harvester):
    harvester.start_new_harvest()
    try:

        update_users(harvester)
        start = time.time()
        logger.info(u"Results computation complete in %ss" % (time.time() - start))

    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s Mem:%s MB" % (harvester,unicode(harvester.get_stats()),unicode(getattr(usage, "ru_maxrss")/(1024.0))))

