# coding=UTF-8

from django.db import models
from datetime import datetime
import time

class Harvester(models.Model):

    class Meta:
        app_label = "harvester"

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=200, null=True)

    user = models.ForeignKey('User', null=True)
    
    consumer_key = models.CharField(max_length=64,null=True)
    consumer_secret = models.CharField(max_length=64,null=True)
    access_token_key = models.CharField(max_length=64,null=True)
    access_token_secret = models.CharField(max_length=64,null=True)

    reset_time = models.DateTimeField(null=True)
    remaining_hist = models.IntegerField(null=True)
    allowed_hit_by_hour = models.IntegerField(null=True)
    next_allowed_harvest_seconds = models.DateTimeField(null=True)

    rate_limit_reached = models.BooleanField()

    is_active = models.BooleanField()

    users_to_harvest = models.ManyToManyField('User', related_name='users_to_harvest', through='Harvester_User')

class Harvester_User(models.Model):

    class Meta:
        app_label = "harvester"

    harvester = models.ForeignKey('Harvester')
    user = models.ForeignKey('User')    

class User(models.Model):

    class Meta:
        app_label = "harvester"

    def __unicode__(self):
        return self.screen_name

    pmk_id =  models.AutoField(primary_key=True)

    id = models.BigIntegerField(null=True)
    name = models.CharField(max_length=200, null=True)
    screen_name = models.CharField(max_length=200, null=True)
    lang = models.CharField(max_length=200, null=True)
    description = models.CharField(max_length=200, null=True)
    url = models.ForeignKey('URL', related_name="user.url", null=True)

    location = models.CharField(max_length=200, null=True)
    time_zone = models.CharField(max_length=200, null=True)
    utc_offset = models.IntegerField(null=True)

    protected = models.BooleanField()

    favourites_count = models.IntegerField(null=True)
    followers_count = models.IntegerField(null=True)
    friends_count = models.IntegerField(null=True)
    statuses_count = models.IntegerField(null=True)
    listed_count = models.IntegerField(null=True)

    created_at = models.DateTimeField(null=True)

    profile_background_color = models.CharField(max_length=200, null=True)
    profile_background_tile = models.BooleanField()
    profile_image_url = models.ForeignKey('URL', related_name="user.profile_image_url", null=True)
    profile_link_color = models.CharField(max_length=200, null=True)
    profile_sidebar_fill_color = models.CharField(max_length=200, null=True)
    profile_text_color = models.CharField(max_length=200, null=True)

    model_update_date = models.DateTimeField(null=True)
    error_triggered = models.BooleanField()

    def update_from_twitter(self, twitter_model):
        model_changed = False
        props_to_check = [
                            "id",
                            "name",
                            "screen_name",
                            "lang",
                            "description",
                            "location",
                            "time_zone",
                            "utc_offset",
                            "protected",
                            "favourites_count",
                            "followers_count",
                            "friends_count",
                            "statuses_count",
                            "listed_count",
                            "profile_background_color",
                            "profile_background_tile",
                            "profile_link_color",
                            "profile_sidebar_fill_color",
                            "profile_text_color",
                            ]

        date_to_check = ["created_at"]
        #TODO implement FK CHECK!!
        fk_to_check = ["url", "profile_image_url"]

        for prop in props_to_check:
            if self.__dict__[prop] != twitter_model.__dict__["_"+prop]:
                self.__dict__[prop] = twitter_model.__dict__["_"+prop]
                model_changed = True

        for prop in date_to_check:
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(twitter_model.__dict__["_"+prop],'%a %b %d %H:%M:%S +0000 %Y'))
            #TODO implement cleaner time comparison
            if str(self.__dict__[prop]) != str(ts):
                self.__dict__[prop] = ts
                model_changed = True

        if model_changed:
            self.model_update_date = datetime.now()
            print "User SAVED!", self
            self.save()

    def get_latest_status(self):

        latest_status = None
        statuses = Status.objects.filter(user=self).order_by("-created_at")
        for latest_status in statuses: break
        return latest_status
        

class Status(models.Model):

    class Meta:
        app_label = "harvester"

    def __unicode__(self):
        return self.text
    pmk_id =  models.AutoField(primary_key=True)

    user = models.ForeignKey('User')

    id = models.BigIntegerField(null=True)
    created_at = models.DateTimeField(null=True)
    favorited = models.BooleanField()
    retweet_count = models.IntegerField(null=True)
    retweeted = models.BooleanField()
    source = models.CharField(max_length=200, null=True)
    text = models.CharField(max_length=200, null=True)
    truncated = models.BooleanField()

    model_update_date = models.DateTimeField(null=True)

    #TODO HASHTAG

    def update_from_twitter(self, twitter_model, user):
        model_changed = False
        props_to_check = [
                            "id",
                            "favorited",
                            "retweet_count",
                            "retweeted",
                            "source",
                            "text",
                            "truncated",
                            ]

        date_to_check = ["created_at"]

        self.user = user        

        for prop in props_to_check:
            if self.__dict__[prop] != twitter_model.__dict__["_"+prop]:
                self.__dict__[prop] = twitter_model.__dict__["_"+prop]
                model_changed = True

        for prop in date_to_check:
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(twitter_model.__dict__["_"+prop],'%a %b %d %H:%M:%S +0000 %Y'))
            #TODO implement cleaner time comparison
            if str(self.__dict__[prop]) != str(ts):
                self.__dict__[prop] = ts
                model_changed = True

        if model_changed:
            self.model_update_date = datetime.now()
            print "Status SAVED!", self
            self.save()
    
class URL(models.Model):

    class Meta:
        app_label = "harvester"

    def __unicode__(self):
        return self.original_url

    original_url = models.CharField(max_length=400,null=True)
    unshorten_url = models.CharField(max_length=400,null=True)
        









