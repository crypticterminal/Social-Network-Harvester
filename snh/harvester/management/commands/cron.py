from django.core.management.base import BaseCommand, CommandError
from harvester.models.twitter import *
from harvester.models import twitterfactory as tf
from django.core.exceptions import ObjectDoesNotExist

import twitter
import pickle

class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    #help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        self.load_twitter_harvester()

    def load_twitter_harvester(self):
        harvester_list = Harvester.objects.all()
        for harvester in harvester_list:
            if harvester.is_active:
                self.run_harvester(harvester)
                
    def run_harvester(self, harvester):
        online = True
        client = None
        if online:
            client = twitter.Api(consumer_key=harvester.consumer_key,
                                consumer_secret=harvester.consumer_secret,
                                access_token_key=harvester.access_token_key,
                                access_token_secret=harvester.access_token_secret,
                                )                

        userlist = harvester.users_to_harvest.all()
        for user in userlist:

            if online and not user.error_triggered:
                try:
                    latest_posts = client.GetUserTimeline(user.screen_name, include_rts=True, include_entities=True)
                except twitter.TwitterError, t:
                    latest_posts = []
                    user.error_triggered = True
                    user.save()
                    print "error", t    
                #output = open('devdata.pkl', 'wb')
                #pickle.dump(latest_posts, output)
                #output.close()
            else:
                pkl_file = open('devdata.pkl', 'rb')
                latest_posts = pickle.load(pkl_file)
                pkl_file.close()

            for tw_status in latest_posts:
                user.update_from_twitter(tw_status.user)
                status = self.get_status(tw_status, user)      
                
        if client is not None:
            self.print_limit(client)

    def get_status(self, tw_status,user):
        try:
            status = Status.objects.get(id__exact=tw_status.id)
        except ObjectDoesNotExist:
            status = Status()
            status.update_from_twitter(tw_status,user)
            print "new"
        return status

    def print_limit(self, client):
        rate = client.GetRateLimitStatus()
        for elem in rate:
            print elem, rate[elem]






        
