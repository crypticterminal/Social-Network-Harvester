# coding=UTF-8

#import sys
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

# coding=UTF-8

from datetime import timedelta
import resource
import time

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from snh.models.dailymotionmodel import *

import snhlogger
logger = snhlogger.init_logger(__name__, "dailymotion_downloader.log")

class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    #help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        try:
            logger.info("Will run the dailymotion video downloader.")

            videos = DMVideo.objects.all()
            for vid in videos:
                logger.info("will extract: %s" % vid.url)
                ret = subprocess.call(["youtube-dl","-oupload/%(id)s.%(ext)s", "%s" % vid.url])
                if ret != 0:
                    logger.info("error:%s" % ret)
                    break
                #break


        except:
            msg = u"Highest exception for the dailymotion video downloader cron. Not good."
            logger.exception(msg)

        logger.info("The harvest has end for the dailymotion video downloader.")



        
