# coding=UTF-8

#import sys
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File

# coding=UTF-8

from datetime import timedelta
import resource
import time
import os

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from snh.models.youtubemodel import *
from settings import MEDIA_ROOT

import snhlogger
logger = snhlogger.init_logger(__name__, "youtube_downloader.log")

class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    #help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        try:
            logger.info("Will run the youtube video downloader.")

            videos = YTVideo.objects.all()
            for vid in videos:
                if True:
                    logger.info("will extract: %s" % vid.swf_url)
                    try:
                        filename = subprocess.check_output(["youtube-dl","-oyoutube_%(id)s.%(ext)s", "--get-filename", "%s" % vid.swf_url])
                        filename = filename.strip("\n")
                        print filename
                        output = subprocess.check_output(["youtube-dl","-oupload/youtube_%(id)s.%(ext)s", "%s" % vid.swf_url])
                        #f = open(os.path.join(MEDIA_ROOT,filename))
                        #myfile = File(f)
                        #vid.video_file.save(filename,myfile,save=False)
                        #vid.save()

                    except subprocess.CalledProcessError:
                        logger.exception(u"cannot download video %s!!", vid.fid)

        except:
            msg = u"Highest exception for the youtube video downloader cron. Not good."
            logger.exception(msg)

        logger.info("The harvest has end for the youtube video downloader.")



        
