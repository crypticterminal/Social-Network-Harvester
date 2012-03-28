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

class YoutubeHarvester(AbstractHaverster):

    ytusers_to_harvest = models.ManyToManyField('YTUser', related_name='ytusers_to_harvest')

    last_harvested_user = models.ForeignKey('YTUser',  related_name='last_harvested_user', null=True)
    current_harvested_user = models.ForeignKey('YTUser', related_name='current_harvested_user',  null=True)

    haverst_deque = None

    def update_client_stats(self):
        self.save()

    def end_current_harvest(self):
        self.update_client_stats()
        if self.current_harvested_user:
            self.last_harvested_user = self.current_harvested_user
        super(DailyMotionHarvester, self).end_current_harvest()

    def api_call(self, method, params):
        super(YoutubeHarvester, self).api_call(method, params)
        return None

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
        all_users = self.ytusers_to_harvest.all()

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
            
class YTUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.screenname

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True)

    uri = models.ForeignKey('URL', related_name="ytuser.uri, null=True)
    age = models.IntegerField(null=True)
    gender = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)

    username = models.CharField(max_length=255, null=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    relationship = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)

    link = models.ManyToMany('URL', related_name="ytuser.link")
    
    company = models.CharField(max_length=255, null=True)
    occupation = models.TextField(null=True)
    school = models.CharField(max_length=255, null=True)
    hobbies = models.TextField(null=True)
    movies = models.TextField(null=True)
    music = models.TextField(null=True)
    books = models.TextField(null=True)
    hometown = models.CharField(max_length=255, null=True)

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

    def update_url_fk(self, self_prop, face_prop, dailymotion_model):
        model_changed = False
        if face_prop in dailymotion_model:
            prop_val = dailymotion_model[face_prop]
            if self_prop is None or self_prop.original_url != prop_val:
                url = None
                try:
                    url = URL.objects.filter(original_url=prop_val)[0]
                except:
                    pass

                if url is None:
                    url = URL(original_url=prop_val)
                    url.save()

                self_prop = url
                model_changed = True
        return model_changed, self_prop

    def update_from_youtube(self, dm_user):
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
                #print "prop changed. %s = %s" % (prop, dm_user[props_to_check[prop]])
                model_changed = True

        for prop in date_to_check:
            if date_to_check[prop] in dm_user and self.__dict__[prop] != dm_user[date_to_check[prop]]:
                date_val = datetime.strptime(dm_user[prop],'%m/%d/%Y')
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        (changed, self_prop) = self.update_url_fk(self.url, "url", dm_user)
        if changed:
            self.url = self_prop
            model_changed = True
                    
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
    
    user = models.ForeignKey('DMUser',  related_name='dmvideo.user')
    
    fid =  models.CharField(max_length=255, null=True)
    title = models.TextField(null=True)
    tag =  models.TextField(null=True)
    tags = models.TextField(null=True)#models.ManyToManyField('Tag', related_name='dmvideo.tags')
    description = models.TextField(null=True)
    language =  models.CharField(max_length=255, null=True)
    country =  models.CharField(max_length=255, null=True)

    url = models.ForeignKey('URL', related_name="dmvideo.url", null=True)
    tiny_url = models.ForeignKey('URL', related_name="dmvideo.tiny_url", null=True)

    created_time = models.DateTimeField(null=True)
    taken_time = models.DateTimeField(null=True)
    modified_time = models.DateTimeField(null=True)

    status =  models.CharField(max_length=255, null=True)
    encoding_progress = models.IntegerField(null=True)
    ftype = models.CharField(max_length=255, null=True)
    paywall = models.BooleanField()
    rental_duration = models.IntegerField(null=True)

    onair = models.BooleanField()
    mode =  models.CharField(max_length=255, null=True)
    live_publish_url = models.ForeignKey('URL', related_name="dmvideo.live_publish_url", null=True)

    private = models.BooleanField()
    explicit = models.BooleanField()

    published = models.BooleanField()
    duration = models.IntegerField(null=True)
    allow_comments = models.BooleanField()

    thumbnail_url = models.ForeignKey('URL', related_name="dmvideo.thumbnail_url", null=True)
    thumbnail_small_url = models.ForeignKey('URL', related_name="dmvideo.thumbnail_small_url", null=True)
    thumbnail_medium_url = models.ForeignKey('URL', related_name="dmvideo.thumbnail_medium_url", null=True)
    thumbnail_large_url = models.ForeignKey('URL', related_name="dmvideo.thumbnail_large_url", null=True)

    rating = models.IntegerField(null=True)
    ratings_total = models.IntegerField(null=True)

    views_total = models.IntegerField(null=True)
    views_last_hour = models.IntegerField(null=True)
    views_last_day = models.IntegerField(null=True)
    views_last_week = models.IntegerField(null=True)
    views_last_month = models.IntegerField(null=True)

    comments_total = models.IntegerField(null=True)
    bookmarks_total = models.IntegerField(null=True)

    embed_html = models.TextField(null=True)
    embed_url = models.ForeignKey('URL', related_name="dmvideo.embed_url", null=True)
    swf_url = models.ForeignKey('URL', related_name="dmvideo.swf_url", null=True)

    aspect_ratio = models.DecimalField(max_digits=13, decimal_places=12, null=True)
    upc = models.CharField(max_length=255, null=True)
    isrc =  models.CharField(max_length=255, null=True)

    geoblocking = models.TextField(null=True)
    in_3d = models.BooleanField()

    def update_url_fk(self, self_prop, face_prop, dailymotion_model):
        model_changed = False
        if face_prop in dailymotion_model:
            prop_val = dailymotion_model[face_prop]
            if self_prop is None or self_prop.original_url != prop_val:
                url = None
                try:
                    url = URL.objects.filter(original_url=prop_val)[0]
                except:
                    pass

                if url is None:
                    url = URL(original_url=prop_val)
                    url.save()

                self_prop = url
                model_changed = True
        return model_changed, self_prop

    def update_from_dailymotion(self, snh_user, dm_video):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"title":u"title",
                            u"tag":u"tag",
                            u"tags":u"tags",
                            u"description":u"description",
                            u"language":u"language",
                            u"country":u"country",
                            u"status":u"status",
                            u"encoding_progress":u"encoding_progress",
                            u"ftype":u"type",
                            u"paywall":u"paywall",
                            u"rental_duration":u"rental_duration",
                            u"onair":u"onair",
                            u"mode":u"mode",
                            u"private":u"private",
                            u"explicit":u"explicit",
                            u"published":u"published",
                            u"duration":u"duration",
                            u"allow_comments":u"allow_comments",
                            u"rating":u"rating",
                            u"ratings_total":u"ratings_total",
                            u"views_total":u"views_total",
                            u"views_last_hour":u"views_last_hour",
                            u"views_last_day":u"views_last_day",
                            u"views_last_week":u"views_last_week",
                            u"views_last_month":u"views_last_month",
                            u"comments_total":u"comments_total",
                            u"bookmarks_total":u"bookmarks_total",
                            u"embed_html":u"embed_html",
                            u"aspect_ratio":u"aspect_ratio",
                            u"upc":u"upc",
                            u"isrc":u"isrc",
                            u"geoblocking":u"geoblocking",
                            u"in_3d":u"3d",
                            }

        date_to_check = {
                            "created_time":"created_time",
                            "taken_time":"taken_time",
                            "modified_time":"modified_time",
                            }

        url_to_check = {
                            self.url:"url",
                            self.tiny_url:"tiny_url",
                            self.live_publish_url:"live_publish_url",
                            self.thumbnail_url:"thumbnail_url",
                            self.thumbnail_small_url:"thumbnail_small_url",
                            self.thumbnail_medium_url:"thumbnail_medium_url",
                            self.thumbnail_large_url:"thumbnail_large_url",
                            self.embed_url:"embed_url",
                            self.swf_url:"swf_url",
                            }

        if self.user != snh_user:
            self.user = snh_user
            model_changed = True

        for prop in props_to_check:
            if props_to_check[prop] in dm_video and unicode(self.__dict__[prop]) != unicode(dm_video[props_to_check[prop]]):
                self.__dict__[prop] = dm_video[props_to_check[prop]]
                model_changed = True

        for prop in date_to_check:
            if date_to_check[prop] in dm_video and self.__dict__[prop] != dm_video[date_to_check[prop]]:
                date_val = datetime.fromtimestamp(float(dm_video[prop]))
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        (changed, self_prop) = self.update_url_fk(self.url, "url", dm_video)
        if changed:
            self.url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.tiny_url, "tiny_url", dm_video)
        if changed:
            self.tiny_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.live_publish_url, "live_publish_url", dm_video)
        if changed:
            self.live_publish_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.thumbnail_url, "thumbnail_url", dm_video)
        if changed:
            self.thumbnail_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.thumbnail_small_url, "thumbnail_small_url", dm_video)
        if changed:
            self.thumbnail_small_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.thumbnail_medium_url, "thumbnail_medium_url", dm_video)
        if changed:
            self.thumbnail_medium_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.thumbnail_large_url, "thumbnail_large_url", dm_video)
        if changed:
            self.thumbnail_large_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.embed_url, "embed_url", dm_video)
        if changed:
            self.embed_url = self_prop
            model_changed = True
            
        (changed, self_prop) = self.update_url_fk(self.swf_url, "swf_url", dm_video)
        if changed:
            self.swf_url = self_prop
            model_changed = True
            
        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed

class DMComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.title

    pmk_id =  models.AutoField(primary_key=True)

    fid =  models.CharField(max_length=255, null=True)

    user = models.ForeignKey('DMUser',  related_name='dmcomment.user', null=True)
    video = models.ForeignKey('DMVideo',  related_name='dmcomment.video')

    message = models.TextField(null=True)
    language =  models.CharField(max_length=255, null=True)
    created_time = models.DateTimeField(null=True)
    locked = models.BooleanField()

    def update_from_dailymotion(self, snh_video, snh_user, dm_comment):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"message":u"message",
                            u"language":u"language",
                            u"locked":u"locked",
                            }

        date_to_check = {
                            "created_time":"created_time",
                            }

        if self.video != snh_video:
            self.video = snh_video
            model_changed = True

        if self.user != snh_user:
            self.user = snh_user
            model_changed = True

        for prop in props_to_check:
            if props_to_check[prop] in dm_comment and unicode(self.__dict__[prop]) != unicode(dm_comment[props_to_check[prop]]):
                self.__dict__[prop] = dm_comment[props_to_check[prop]]
                model_changed = True

        for prop in date_to_check:
            if date_to_check[prop] in dm_comment and self.__dict__[prop] != dm_comment[date_to_check[prop]]:
                date_val = datetime.fromtimestamp(float(dm_comment[prop]))
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed









