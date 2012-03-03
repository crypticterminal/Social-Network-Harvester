# coding=UTF-8

from django.db import models
from datetime import datetime
import time

from snh.models.common import *

class TwitterHarvester(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.name

    pmk_id =  models.AutoField(primary_key=True)

    name = models.CharField(max_length=255, null=True)

    user = models.ForeignKey('TWUser', null=True)
    
    consumer_key = models.CharField(max_length=255,null=True)
    consumer_secret = models.CharField(max_length=255,null=True)
    access_token_key = models.CharField(max_length=255,null=True)
    access_token_secret = models.CharField(max_length=255,null=True)

    reset_time = models.DateTimeField(null=True)
    remaining_hist = models.IntegerField(null=True)
    allowed_hit_by_hour = models.IntegerField(null=True)
    next_allowed_harvest_seconds = models.DateTimeField(null=True)

    rate_limit_reached = models.BooleanField()

    is_active = models.BooleanField()

    twusers_to_harvest = models.ManyToManyField('TWUser', related_name='twusers_to_harvest')

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
                            "fid":"id",
                            "name":"name",
                            "screen_name":"screen_name",
                            "lang":"lang",
                            "description":"description",
                            "location":"location",
                            "time_zone":"time_zone",
                            "utc_offset":"utc_offset",
                            "protected":"protected",
                            "favourites_count":"favourites_count",
                            "followers_count":"followers_count",
                            "friends_count":"friends_count",
                            "statuses_count":"statuses_count",
                            "listed_count":"listed_count",
                            "profile_background_color":"profile_background_color",
                            "profile_background_tile":"profile_background_tile",
                            "profile_link_color":"profile_link_color",
                            "profile_sidebar_fill_color":"profile_sidebar_fill_color",
                            "profile_text_color":"profile_text_color",
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
                            "fid":"id",
                            "favorited":"favorited",
                            "retweet_count":"retweet_count",
                            "retweeted":"retweeted",
                            "source":"source",
                            "text":"text",
                            "truncated":"truncated",
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


