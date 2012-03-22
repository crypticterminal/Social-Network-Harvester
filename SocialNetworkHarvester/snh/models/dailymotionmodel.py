# coding=UTF-8
from collections import deque
from datetime import datetime
import time

from httplib2 import Http
from urllib import urlencode
import json
import urllib2

from django.db import models
from snh.models.common import *

class DailyMotionHarvester(AbstractHaverster):

    base = 'https://api.dailymotion.com/json'
    oauth = 'https://api.dailymotion.com/oauth/token'

    key = models.CharField(max_length=255, null=True)
    secret = models.CharField(max_length=255, null=True)
    user = models.CharField(max_length=255, null=True)
    password = models.CharField(max_length=255, null=True)

    access_token = None
    refresh_token = None
    uurl = None

    dmusers_to_harvest = models.ManyToManyField('DMUser', related_name='dmusers_to_harvest')

    last_harvested_user = models.ForeignKey('DMUser',  related_name='last_harvested_user', null=True)
    current_harvested_user = models.ForeignKey('DMUser', related_name='current_harvested_user',  null=True)

    haverst_deque = None

    def get_token(self):
        if not self.access_token:
            values = {'grant_type' : 'password',
                      'client_id' : self.key,
                      'client_secret' : self.secret,
                      'username' : self.user,
                      'password' : self.password,
                      'scope':'write'
                      }

            data = urlencode(values)
            req = urllib2.Request(self.oauth, data)
            response = urllib2.urlopen(req)

            result=json.load(response)
            self.access_token = result['access_token']
            self.refresh_token = result['refresh_token']

            self.uurl='?access_token=' + self.access_token
            
        return self.uurl

    def update_client_stats(self):
        self.save()

    def end_current_harvest(self):
        self.update_client_stats()
        if self.current_harvested_user:
            self.last_harvested_user = self.current_harvested_user
        super(DailyMotionHarvester, self).end_current_harvest()

    def check_error(self, result):
        #Unrecognized value ()...
        #Unsufficient scope for `fields' parameter
        if result:
            if type(result) == dict:
                if "error" not in result:
                    return result
                else:
                    raise Exception("DMError:(%s)-[%s] %s!!!" % (result["error"]["code"],result["error"]["type"], result["error"]["message"]))
            else:
                raise Exception("Result is not a dict!!!")
        else:
            raise Exception("Empty result!!!")

    def api_call(self, method, params):
        super(DailyMotionHarvester, self).api_call(method, params)

        job=json.dumps({"call":"%s %s" % (method, params),"args":None})
        req = urllib2.Request(self.base+self.get_token(), job, {'content-type': 'application/json'})
        response = urllib2.urlopen(req)
        result=json.load(response)

        return self.check_error(result)

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
        all_users = self.dmusers_to_harvest.all()

        if self.last_harvested_user:
            count = 0
            for user in all_users:
                if user == self.last_harvested_user:
                    break
                count = count + 1
            retry_last_on_fail = 1 if self.retry_user_after_abortion and self.last_user_harvest_was_aborted else 0
            self.haverst_deque.extend(all_users[count+retry_last_on_fail:])
            self.haverst_deque.extend(all_users[:count+retry_last_on_fail])
        else:
            self.haverst_deque.extend(all_users)

    def get_stats(self):
        parent_stats = super(TwitterHarvester, self).get_stats()
        parent_stats["concrete"] = {}
        return parent_stats
            
class DMUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.screenname

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, null=True)
    screenname = models.CharField(max_length=255, null=True)
    gender = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    language = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=255, null=True)
    ftype = models.CharField(max_length=255, null=True)

    url = models.ForeignKey('URL', related_name="dmuser.url", null=True)

    avatar_small_url = models.ForeignKey('URL', related_name="dmuser.avatar_small_url", null=True)
    avatar_medium_url = models.ForeignKey('URL', related_name="dmuser.avatar_medium_url", null=True)
    avatar_large_url = models.ForeignKey('URL', related_name="dmuser.avatar_large_url", null=True)

    videostar = models.ForeignKey('DMVideo', related_name="dmuser.videostar", null=True)
    views_total = models.IntegerField(null=True)
    videos_total = models.IntegerField(null=True)
    created_time = models.DateTimeField(null=True)

    error_triggered = models.BooleanField()
    updated_time = models.DateTimeField(null=True)

    def update_from_dailymotion(self, dm_user):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"screenname":u"screenname",
                            u"username":u"username",
                            u"gender":u"gender",
                            u"description":u"description",
                            u"language":u"language",
                            u"status":u"status",
                            u"views_total":u"views_total",
                            u"videos_total":u"videos_total",
                            u"ftype":u"type",
                            }

        #date_to_check = {"created_time":"created_time"}
        date_to_check = {}

        for prop in props_to_check:
            if props_to_check[prop] in dm_user and unicode(self.__dict__[prop]) != unicode(dm_user[props_to_check[prop]]):
                self.__dict__[prop] = dm_user[props_to_check[prop]]
                print "prop changed. %s = %s" % (prop, dm_user[props_to_check[prop]])
                model_changed = True

        for prop in date_to_check:
            if date_to_check[prop] in dm_user and self.__dict__[prop] != dm_user[date_to_check[prop]]:
                date_val = datetime.strptime(dm_user[prop],'%m/%d/%Y')
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        #(changed, self_prop) = self.update_url_fk(self.website, "website", dm_user)
        #if changed:
        #    self.website = self_prop
        #    model_changed = True
            
        if model_changed:
            self.model_update_date = datetime.utcnow()
            #print self.pmk_id, self.fid, self, self.__dict__, dm_user
            self.save()

        return model_changed


class DMVideo(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.title

    pmk_id =  models.AutoField(primary_key=True)
    
    user = models.ForeignKey('DMUser',  related_name='dmvideo.user', null=True)

    embed_html = models.TextField(null=True)
    rating = models.IntegerField(null=True)
    ratings_total = models.IntegerField(null=True)
    comments_total = models.IntegerField(null=True)
    views_last_day = models.IntegerField(null=True)
    private = models.BooleanField()

    created_time = models.DateTimeField(null=True)
    taken_time = models.DateTimeField(null=True)
    modified_time = models.DateTimeField(null=True)

    views_total = models.IntegerField(null=True)
    views_last_hour = models.IntegerField(null=True)
    duration = models.IntegerField(null=True)
    geoblocking = models.TextField(null=True)
    fid =  models.CharField(max_length=255, null=True)
    thumbnail_large_url = models.ForeignKey('URL', related_name="dmvideo.thumbnail_large_url", null=True)
    paywall = models.BooleanField()
    swf_url = models.ForeignKey('URL', related_name="dmvideo.swf_url", null=True)
    encoding_progress = models.IntegerField(null=True)
    views_last_month = models.IntegerField(null=True)
    ftype = models.CharField(max_length=255, null=True)
    
    #channel = news',
    #channel.name = News',
    #channel.id = news',
    #channel.description = models.TextField(null=True)

    in_3d = models.BooleanField()
    status =  models.CharField(max_length=255, null=True)
    embed_url = models.ForeignKey('URL', related_name="dmvideo.embed_url", null=True)
    description = models.TextField(null=True)
    tags = models.ManyToManyField('Tag', related_name='dmvideo.tags')
    live_publish_url = models.ForeignKey('URL', related_name="dmvideo.live_publish_url", null=True)
    isrc =  models.CharField(max_length=255, null=True)
    bookmarks_total = models.IntegerField(null=True)
    views_last_week = models.IntegerField(null=True)
    allow_comments = models.BooleanField()
    onair = models.BooleanField()
    language =  models.CharField(max_length=255, null=True)
    country =  models.CharField(max_length=255, null=True)
    title = models.TextField(null=True)
    explicit = models.BooleanField()
    upc = models.CharField(max_length=255, null=True)
    url = models.ForeignKey('URL', related_name="dmvideo.url", null=True)
    rental_duration = models.IntegerField(null=True)
    mode =  models.CharField(max_length=255, null=True)
    published = models.BooleanField()
    aspect_ratio = models.DecimalField(max_digits=13, decimal_places=12)

class DMComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.title

    pmk_id =  models.AutoField(primary_key=True)

    user = models.ForeignKey('DMUser',  related_name='dmcomment.user', null=True)
    video = models.ForeignKey('DMVideo',  related_name='dmcomment.video', null=True)

    message = models.TextField(null=True)










