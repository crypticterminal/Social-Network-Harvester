# coding=UTF-8
from collections import deque
from datetime import datetime
import time

import gdata.youtube
import gdata.youtube.service

from django.db import models
from snh.models.common import *

class YoutubeHarvester(AbstractHaverster):

    ytusers_to_harvest = models.ManyToManyField('YTUser', related_name='ytusers_to_harvest')

    last_harvested_user = models.ForeignKey('YTUser',  related_name='last_harvested_user', null=True)
    current_harvested_user = models.ForeignKey('YTUser', related_name='current_harvested_user',  null=True)

    client = gdata.youtube.service.YouTubeService()

    haverst_deque = None

    def update_client_stats(self):
        self.save()

    def end_current_harvest(self):
        self.update_client_stats()
        if self.current_harvested_user:
            self.last_harvested_user = self.current_harvested_user
        super(YoutubeHarvester, self).end_current_harvest()

    def api_call(self, method, params):
        super(YoutubeHarvester, self).api_call(method, params)
        metp = getattr(self.client, method)
        ret = metp(**params)
        return ret

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
        parent_stats = super(YoutubeHarvester, self).get_stats()
        parent_stats["concrete"] = {}
        return parent_stats
            
class YTUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.screenname

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True)

    uri = models.ForeignKey('URL', related_name="ytuser.uri", null=True)
    age = models.IntegerField(null=True)
    gender = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)

    username = models.CharField(max_length=255, null=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    relationship = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)

    link = models.ManyToManyField('URL', related_name="ytuser.link")
    
    company = models.CharField(max_length=255, null=True)
    occupation = models.TextField(null=True)
    school = models.CharField(max_length=255, null=True)
    hobbies = models.TextField(null=True)
    movies = models.TextField(null=True)
    music = models.TextField(null=True)
    books = models.TextField(null=True)
    hometown = models.CharField(max_length=255, null=True)

    error_triggered = models.BooleanField()
    updated_time = models.DateTimeField(null=True)

    def update_url_fk(self, self_prop, face_prop, Youtube_model):
        model_changed = False
        if face_prop in Youtube_model:
            prop_val = Youtube_model[face_prop]
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

    def isUTF8(self, text):
        try:
            text = unicode(text, 'UTF-8', 'strict')
            return True
        except UnicodeDecodeError:
            return False
    def update_from_youtube(self, yt_user):
        model_changed = False
        props_to_check = {
                            u"gender":u"gender",
                            u"location":u"location",
                            u"username":u"username",
                            u"first_name":u"first_name",
                            u"last_name":u"last_name",
                            u"relationship":u"relationship",
                            u"description":u"description",
                            u"company":u"company",
                            u"occupation":u"occupation",
                            u"school":u"school",
                            u"hobbies":u"hobbies",
                            u"music":u"music",
                            u"books":u"books",
                            u"hometown":u"hometown",
                            }

        if yt_user.age and \
                yt_user.age.text and \
                self.age != int(yt_user.age.text):
            self.age = int(yt_user.age.text)
            print "age change %d" % self.age 
            model_changed = True

        for prop in props_to_check:
            if props_to_check[prop] in yt_user.__dict__ and \
                    yt_user.__dict__[props_to_check[prop]] and \
                    yt_user.__dict__[props_to_check[prop]].text and \
                    self.__dict__[prop] != unicode(yt_user.__dict__[props_to_check[prop]].text, 'UTF-8'):

                if not self.isUTF8(yt_user.__dict__[props_to_check[prop]].text):
                    print "UTF", prop

                self.__dict__[prop] = unicode(yt_user.__dict__[props_to_check[prop]].text, 'UTF-8')
                print "prop changed. %s = %s" % (prop, self.__dict__[prop]) 
                model_changed = True
            
        if model_changed:
            self.model_update_date = datetime.utcnow()
            #print self.pmk_id, self.fid, self, self.__dict__, yt_user
            self.save()

        return model_changed

class YTVideo(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.title

    pmk_id =  models.AutoField(primary_key=True)
    
    user = models.ForeignKey('YTUser',  related_name='ytvideo.user')
    fid =  models.CharField(max_length=255, null=True)
    uri = models.ForeignKey('URL', related_name="ytvideo.uri", null=True)

    def update_url_fk(self, self_prop, face_prop, Youtube_model):
        model_changed = False
        if face_prop in Youtube_model:
            prop_val = Youtube_model[face_prop]
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

    def update_from_youtube(self, snh_user, dm_video):
        model_changed = False
        props_to_check = {
                            u"description":u"description",
                            }

        if yt_user.age and \
                yt_user.age.text and \
                self.age != int(yt_user.age.text):
            self.age = int(yt_user.age.text)
            print "age change %d" % self.age 
            model_changed = True

        for prop in props_to_check:
            if props_to_check[prop] in yt_user.__dict__ and \
                    yt_user.__dict__[props_to_check[prop]] and \
                    yt_user.__dict__[props_to_check[prop]].text and \
                    self.__dict__[prop] != unicode(yt_user.__dict__[props_to_check[prop]].text, 'UTF-8'):

                if not self.isUTF8(yt_user.__dict__[props_to_check[prop]].text):
                    print "UTF", prop

                self.__dict__[prop] = unicode(yt_user.__dict__[props_to_check[prop]].text, 'UTF-8')
                print "prop changed. %s = %s" % (prop, self.__dict__[prop]) 
                model_changed = True
            
        if model_changed:
            self.model_update_date = datetime.utcnow()
            #print self.pmk_id, self.fid, self, self.__dict__, yt_user
            self.save()

        return model_changed

class YTComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.title

    pmk_id =  models.AutoField(primary_key=True)

    fid =  models.CharField(max_length=255, null=True)

    user = models.ForeignKey('YTUser',  related_name='ytcomment.user', null=True)
    video = models.ForeignKey('DMVideo',  related_name='ytcomment.video')
    message = models.TextField(null=True)


    def update_from_Youtube(self, snh_video, snh_user, yt_comment):
        model_changed = False
        props_to_check = {
                            u"message":u"message",
                            }

        date_to_check = {
                            #"created_time":"created_time",
                            }

        if self.video != snh_video:
            self.video = snh_video
            model_changed = True

        if self.user != snh_user:
            self.user = snh_user
            model_changed = True

        for prop in props_to_check:
            if props_to_check[prop] in yt_comment and unicode(self.__dict__[prop]) != unicode(yt_comment[props_to_check[prop]]):
                self.__dict__[prop] = yt_comment[props_to_check[prop]]
                model_changed = True

        for prop in date_to_check:
            if date_to_check[prop] in yt_comment and self.__dict__[prop] != yt_comment[date_to_check[prop]]:
                date_val = datetime.fromtimestamp(float(yt_comment[prop]))
                if self.__dict__[prop] != date_val:
                    self.__dict__[prop] = date_val
                    model_changed = True

        if model_changed:
            self.model_update_date = datetime.utcnow()
            self.save()

        return model_changed









