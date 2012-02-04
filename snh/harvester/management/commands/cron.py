from django.core.management.base import BaseCommand, CommandError
from harvester.models.twitter import *

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
        if online:        
            client = twitter.Api(consumer_key=harvester.consumer_key,
                                consumer_secret=harvester.consumer_secret,
                                access_token_key=harvester.access_token_key,
                                access_token_secret=harvester.access_token_secret,
                                )                
        for username in harvester.users_to_harvest.all():
            if online:
                latest_posts = client.GetUserTimeline(username, include_rts=True, include_entities=True)
                output = open('devdata.pkl', 'wb')
                pickle.dump(latest_posts, output)
                output.close()
            else:
                pkl_file = open('devdata.pkl', 'rb')
                latest_posts = pickle.load(pkl_file)
                pkl_file.close()

            user = User.objects.filter(name__exact=username)[0]
            print latest_posts









        
