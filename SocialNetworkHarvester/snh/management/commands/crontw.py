# coding=UTF-8

import sys
import os
import logging
import traceback

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from snh.management.commands.cronharvester import twitterch
from snh.management.commands.cronharvester import facebookch

from settings import PROJECT_PATH

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(os.path.join(PROJECT_PATH, "log/twitter.log"), mode="a+")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    #help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        try:
            logger.info("Will run the Twitter harvesters.")
            twitterch.run_twitter_harvester()
        except:
            msg = u"Highest exception for the twitter cron. Not good."
            logger.exception(msg)

        logger.info("The harvest has end for the Twitter harvesters.")



        
