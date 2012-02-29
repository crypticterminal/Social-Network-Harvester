from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from snh.management.commands.cronharvester import twitterch

class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    #help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        twitterch.run_twitter_harvester()







        
