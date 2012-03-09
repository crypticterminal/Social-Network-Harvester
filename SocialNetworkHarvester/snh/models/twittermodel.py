# coding=UTF-8
from collections import deque
from django.db import models
from datetime import datetime
import time
import twitter as pytw

from snh.models.common import *

class TwitterHarvester(AbstractHaverster):

    client = None

    consumer_key = models.CharField(max_length=255,null=True)
    consumer_secret = models.CharField(max_length=255,null=True)
    access_token_key = models.CharField(max_length=255,null=True)
    access_token_secret = models.CharField(max_length=255,null=True)

    remaining_hits = models.IntegerField(null=True)
    reset_time_in_seconds = models.DateTimeField(null=True)
    hourly_limit = models.IntegerField(null=True)
    reset_time = models.DateTimeField(null=True)

    twusers_to_harvest = models.ManyToManyField('TWUser', related_name='twusers_to_harvest')

    last_harvested_user = models.ForeignKey('TWUser',  related_name='last_harvested_user', null=True)
    current_harvested_user = models.ForeignKey('TWUser', related_name='current_harvested_user',  null=True)

    haverst_deque = None

    def gie(self, d, k):
        return d[k] if k in d else None 

    def get_client(self):
        if not self.client:
            self.client = pytw.Api(consumer_key=self.consumer_key,
                                        consumer_secret=self.consumer_secret,
                                        access_token_key=self.access_token_key,
                                        access_token_secret=self.access_token_secret,
                                     )
        if not self.client:
            raise Exception("Cannot initialize the twitter client :(")
        return self.client

    def update_client_stats(self):
        c = self.get_client()
        rate = c.GetRateLimitStatus()
        self.remaining_hits = gie(rate, "remaining_hits")
        self.reset_time_in_seconds =gie(rate, "reset_time_in_seconds")
        self.hourly_limit = gie(rate, "hourly_limit")
        self.reset_time = gie(rate, "reset_time")
        self.save()

    def ending_current_harvest(self):
        #self.update_client_stats()
        super(TwitterHarvester, self).ending_current_harvest()

    def api_call(self, method, params):
        super(TwitterHarvester, self).api_call(method, params)
        c = self.get_client()   
        metp = getattr(c, method)
        metp(*params)

    def get_last_harvested_user(self):
        return self.last_harvested_user
    
    def get_current_harvested_user(self):
        return self.current_harvested_user

    def get_next_user_to_harvest(self):

        if self.current_harvested_user:
            self.last_harvested_user = self.current_harvested_user

        if self.haverst_deque is None:
            self.build_harvester_sequence()

        try:
            self.current_harvested_user = self.haverst_deque.pop()
        except IndexError:
            self.current_harvested_user = None

        self.update_client_stats()
        return self.current_harvested_user

    def build_harvester_sequence(self):
        self.haverst_deque = deque()
        all_users = self.twusers_to_harvest.all()

        if self.last_harvested_user:
            count = 0
            for user in all_users:
                if user == self.last_harvested_user:
                    break
                count = count + 1
            self.haverst_deque.extend(all_users[count:])
            self.haverst_deque.extend(all_users[:count])
        else:
            self.haverst_deque.extend(all_users)
            

class TWUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.screen_name

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.BigIntegerField(null=True, unique=True)
    name = models.CharField(max_length=255, null=True)
    screen_name = models.CharField(max_length=255, unique=True, null=True)
    lang = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    url = models.ForeignKey('URL', related_name="twuser.url", null=True)

    location = models.TextField(null=True)
    time_zone = models.TextField(null=True)
    utc_offset = models.IntegerField(null=True)

    protected = models.BooleanField()

    favourites_count = models.IntegerField(null=True)
    followers_count = models.IntegerField(null=True)
    friends_count = models.IntegerField(null=True)
    statuses_count = models.IntegerField(null=True)
    listed_count = models.IntegerField(null=True)

    created_at = models.DateTimeField(null=True)

    profile_background_color = models.CharField(max_length=255, null=True)
    profile_background_tile = models.BooleanField()
    profile_image_url = models.ForeignKey('URL', related_name="twuser.profile_image_url", null=True)
    profile_link_color = models.CharField(max_length=255, null=True)
    profile_sidebar_fill_color = models.CharField(max_length=255, null=True)
    profile_text_color = models.CharField(max_length=255, null=True)

    model_update_date = models.DateTimeField(null=True)
    error_triggered = models.BooleanField()

    def update_from_twitter(self, twitter_model):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"name":u"name",
                            u"screen_name":u"screen_name",
                            u"lang":u"lang",
                            u"description":u"description",
                            u"location":u"location",
                            u"time_zone":u"time_zone",
                            u"utc_offset":u"utc_offset",
                            u"protected":u"protected",
                            u"favourites_count":u"favourites_count",
                            u"followers_count":u"followers_count",
                            u"friends_count":u"friends_count",
                            u"statuses_count":u"statuses_count",
                            u"listed_count":u"listed_count",
                            u"profile_background_color":u"profile_background_color",
                            u"profile_background_tile":u"profile_background_tile",
                            u"profile_link_color":u"profile_link_color",
                            u"profile_sidebar_fill_color":u"profile_sidebar_fill_color",
                            u"profile_text_color":u"profile_text_color",
                            }

        date_to_check = ["created_at"]
        #TODO implement FK CHECK!!
        fk_to_check = ["url", "profile_image_url"]

        for prop in props_to_check:
            if self.__dict__[prop] != twitter_model.__dict__["_"+props_to_check[prop]]:
                self.__dict__[prop] = twitter_model.__dict__["_"+props_to_check[prop]]
                model_changed = True

        for prop in date_to_check:
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(twitter_model.__dict__["_"+prop],'%a %b %d %H:%M:%S +0000 %Y'))
            #TODO implement cleaner time comparison
            if str(self.__dict__[prop]) != str(ts):
                self.__dict__[prop] = ts
                model_changed = True

        if model_changed:
            self.model_update_date = datetime.now()
            #print "User SAVED!", self
            self.save()

    def get_latest_status(self):

        latest_status = None
        statuses = TWStatus.objects.filter(user=self).order_by("-created_at")
        for latest_status in statuses: break
        return latest_status
        

class TWStatus(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.text

    pmk_id =  models.AutoField(primary_key=True)

    user = models.ForeignKey('TWUser')

    fid = models.BigIntegerField(null=True)
    created_at = models.DateTimeField(null=True)
    favorited = models.BooleanField()
    retweet_count = models.IntegerField(null=True)
    retweeted = models.BooleanField()
    source = models.TextField(null=True)
    text = models.TextField(null=True)
    truncated = models.BooleanField()

    model_update_date = models.DateTimeField(null=True)

    #TODO HASHTAG

    def update_from_twitter(self, twitter_model, user):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"favorited":u"favorited",
                            u"retweet_count":u"retweet_count",
                            u"retweeted":u"retweeted",
                            u"source":u"source",
                            u"text":u"text",
                            u"truncated":u"truncated",
                            }

        date_to_check = ["created_at"]

        self.user = user

        for prop in props_to_check:
            if self.__dict__[prop] != twitter_model.__dict__["_"+props_to_check[prop]]:
                self.__dict__[prop] = twitter_model.__dict__["_"+props_to_check[prop]]
                model_changed = True

        for prop in date_to_check:
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(twitter_model.__dict__["_"+prop],'%a %b %d %H:%M:%S +0000 %Y'))
            #TODO implement cleaner time comparison
            if str(self.__dict__[prop]) != str(ts):
                self.__dict__[prop] = ts
                model_changed = True

        if model_changed:
            self.model_update_date = datetime.now()
            #print "Status SAVED!", self
            self.save()


