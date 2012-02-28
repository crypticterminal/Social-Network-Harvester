from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

#from harvester.models.twitter import *
#from harvester.models import twitterfactory as tf

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
        client = twitter.Api(consumer_key=harvester.consumer_key,
                            consumer_secret=harvester.consumer_secret,
                            access_token_key=harvester.access_token_key,
                            access_token_secret=harvester.access_token_secret,
                            )                

        userlist = harvester.users_to_harvest.all()
        for user in userlist:
            latest_statuses = []

            if not user.error_triggered:
                try:

                    latest_status = user.get_latest_status()
                    latest_status_id = None if latest_status is None else latest_status.id
                    latest_statuses = client.GetUserTimeline(
                                                                screen_name=user.screen_name, 
                                                                since_id=latest_status_id, 
                                                                include_rts=True, 
                                                                include_entities=True
                                                            )
                except twitter.TwitterError, t:
                    user.error_triggered = True
                    user.save()
                    print "ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry" % user
            else:
                print "ERROR: the user %s was reject due to error. Please remove the error_triggered flag to retry" % user
 
            for tw_status in latest_statuses:
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
            print "new", status
        return status

    def print_limit(self, client):
        rate = client.GetRateLimitStatus()
        for elem in rate:
            print elem, rate[elem]






        
