# coding=UTF-8

import sys
import traceback

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from snh.management.commands.cronharvester import twitterch
from snh.management.commands.cronharvester import facebookch

class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    #help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        try:
            twitterch.run_twitter_harvester()
            facebookch.run_facebook_harvester()
        except Exception, e:
            print u"not good. The Highest of the Highest level of exception. The havest is compromised :( %s" % e
            traceback.print_exc()





        
