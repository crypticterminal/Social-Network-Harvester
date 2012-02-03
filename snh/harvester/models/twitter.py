# coding=UTF-8

from django.db import models

class Harvester(models.Model):

    class Meta:
        app_label = "harvester"

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=200)

    user = models.ForeignKey('User', null=True)
    
    consumer_key = models.CharField(max_length=64)
    consumer_secret = models.CharField(max_length=64)
    access_token_key = models.CharField(max_length=64)
    access_token_secret = models.CharField(max_length=64)

    reset_time = models.DateTimeField(null=True)
    remaining_hist = models.IntegerField(null=True)
    allowed_hit_by_hour = models.IntegerField(null=True)
    next_allowed_harvest_seconds = models.DateTimeField(null=True)

    rate_limit_reached = models.BooleanField()

    users_to_harvest = models.ManyToManyField('User', related_name='harvester.users_to_harvest', through='Harvester_User')

class Harvester_User(models.Model):

    class Meta:
        app_label = "harvester"

    harvester = models.ForeignKey('Harvester')
    user = models.ForeignKey('User')    

class User(models.Model):

    class Meta:
        app_label = "harvester"

    def __unicode__(self):
        return self.name

    twitter_id = models.IntegerField(null=True)
    name = models.CharField(max_length=200)
    screenanme = models.CharField(max_length=200)
    lang = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    url = models.ForeignKey('URL', related_name="user.url", null=True)

    location = models.CharField(max_length=200)
    timezone = models.CharField(max_length=200)
    utc_offset = models.IntegerField(null=True)

    protected = models.BooleanField()

    favourites_count = models.IntegerField(null=True)
    followers_count = models.IntegerField(null=True)
    friends_count = models.IntegerField(null=True)
    statuses_count = models.IntegerField(null=True)
    listed_count = models.IntegerField(null=True)

    user_creation_date = models.DateTimeField(null=True)
    model_update_date = models.DateTimeField(null=True)

    profile_background_color = models.CharField(max_length=200)
    profile_background_tile = models.BooleanField()
    profile_image_url = models.ForeignKey('URL', related_name="user.profile_image_url", null=True)
    profile_link_color = models.CharField(max_length=200)
    profile_sidebar_fill_color = models.CharField(max_length=200)
    profile_text_color = models.CharField(max_length=200)

class Status(models.Model):

    class Meta:
        app_label = "harvester"

    def __unicode__(self):
        return self.text

    user = models.ForeignKey('User')

    status_id = models.IntegerField(null=True)
    creation_date = models.DateTimeField(null=True)
    favorited = models.BooleanField()
    retweeted_count = models.IntegerField(null=True)
    source = models.CharField(max_length=200)
    text = models.CharField(max_length=200)
    truncated = models.BooleanField()
    
class URL(models.Model):

    class Meta:
        app_label = "harvester"

    def __unicode__(self):
        return self.original_url

    original_url = models.CharField(max_length=400)
    unshorten_url = models.CharField(max_length=400)
        









