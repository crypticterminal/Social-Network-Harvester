# coding=UTF-8

from django.db import models
from datetime import datetime
import time

from snh.models.common import *

class FacebookHarvester(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.name

    pmk_id =  models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True)
    is_active = models.BooleanField()
    fbusers_to_harvest = models.ManyToManyField('FBUser', related_name='fbusers_to_harvest')

class FBUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return unicode(self.username)
   
    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True, unique=True)
    name = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, null=True)
    website = models.ForeignKey('URL', related_name="fbuser.website", null=True)
    link = models.ForeignKey('URL', related_name="fbuser.link", null=True)

    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    gender = models.CharField(max_length=255, null=True)
    locale = models.CharField(max_length=255, null=True)
    languages_raw = models.TextField(null=True) #not supported but saved
    third_party_id = models.CharField(max_length=255, null=True)
    installed_raw = models.TextField(null=True) #not supported but saved
    timezone_raw = models.TextField(null=True) #not supported but saved
    updated_time = models.DateTimeField(null=True)
    verified = models.BooleanField()
    bio = models.TextField(null=True)
    birthday = models.DateTimeField(null=True)
    education_raw = models.TextField(null=True) #not supported but saved
    email = models.CharField(max_length=255, null=True)
    hometown = models.CharField(max_length=255, null=True)
    interested_in_raw = models.TextField(null=True) #not supported but saved
    location_raw = models.TextField(null=True) #not supported but saved
    political = models.TextField(null=True)
    favorite_athletes_raw = models.TextField(null=True) #not supported but saved
    favorite_teams_raw = models.TextField(null=True) #not supported but saved
    quotes = models.TextField(max_length=255, null=True)
    relationship_status = models.TextField(null=True)
    religion = models.TextField(null=True)
    significant_other_raw = models.TextField(null=True) #not supported but saved
    video_upload_limits_raw = models.TextField(null=True) #not supported but saved
    work_raw = models.TextField(null=True) #not supported but saved

    category = models.TextField(null=True)
    likes = models.IntegerField(null=True)
    about = models.TextField(null=True)
    phone = models.CharField(max_length=255, null=True)
    checkins = models.IntegerField(null=True)
    picture = models.ForeignKey('URL', related_name="fbpagedesc.picture", null=True)
    talking_about_count = models.IntegerField(null=True)

    error_triggered = models.BooleanField()

    def update_from_facebook(self, fb_user):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"name":u"name",
                            u"username":u"username",
                            u"first_name":u"first_name",
                            u"last_name":u"last_name",
                            u"gender":u"gender",
                            u"locale":u"locale",
                            u"languages_raw":u"languages",
                            u"third_party_id":u"third_party_id",
                            u"installed_raw":u"installed",
                            u"timezone_raw":u"timezone",
                            u"verified":u"verified",
                            u"bio":u"bio",
                            u"education_raw":u"educaction",
                            u"email":u"email",
                            u"hometown":u"hometown",
                            u"interested_in_raw":u"interested_in",
                            u"location_raw":u"location",
                            u"political":u"political",
                            u"favorite_athletes_raw":u"favorite_athletes",
                            u"favorite_teams":u"favorite_teams",
                            u"quotes":u"quotes",
                            u"relationship_status":u"relationship_status",
                            u"religion":u"religion",
                            u"significant_other_raw":u"significant_other",
                            u"video_upload_limits_raw":u"video_upload_limits",
                            u"work_raw":u"work",
                            u"category":u"category",
                            u"likes":u"likes",
                            u"location_raw":u"location",
                            u"phone":u"phone",
                            u"checkins":u"checkins",
                            u"about":u"about",
                            u"talking_about_count":u"talking_about_count",
                            }

        #date_to_check = {"birthday":"birthday"}
        date_to_check = {}
        
        for prop in props_to_check:
            if props_to_check[prop] in fb_user and unicode(self.__dict__[prop]) != unicode(fb_user[props_to_check[prop]]):
                old_val = self.__dict__[prop]
                self.__dict__[prop] = fb_user[props_to_check[prop]]
                print "prop changed. %s was %s is %s" % (prop, old_val, self.__dict__[prop])
                model_changed = True

        for prop in date_to_check:
            if date_to_check[prop] in fb_user and self.__dict__[prop] != fb_user[date_to_check[prop]]:
                #TODO error in translation. Always triggers a value changed...
                ts = time.strftime('%Y-%m-%d', time.strptime(fb_user[prop],'%m/%d/%Y'))
                #TODO implement cleaner time comparison
                if str(self.__dict__[prop]) != str(ts):
                    old_val = self.__dict__[prop]
                    self.__dict__[prop] = ts
                    print "prop changed. %s was %s is %s" % (prop, old_val, self.__dict__[prop])
                    model_changed = True

        if self.fid == self.username and self.name:
            self.username = self.name
            model_changed = True


        if model_changed:
            self.model_update_date = datetime.now()
            self.save()
            print u"User SAVED!", self

        return model_changed

class FBPost(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.ftype

    pmk_id =  models.AutoField(primary_key=True)
    user = models.ForeignKey('FBUser')

    fid = models.CharField(max_length=255, null=True, unique=True)
    ffrom = models.ForeignKey('FBUser', related_name='fbpost.from', null=True)
    to = models.ManyToManyField('FBUser', related_name='fbpost.to', null=True)
    message = models.TextField(null=True)
    message_tags_raw = models.TextField(null=True) #not supported but saved
    picture = models.ForeignKey('URL', related_name="fbpost.picture", null=True)
    link = models.ForeignKey('URL', related_name="fbpost.link", null=True)
    name = models.CharField(max_length=255, null=True)
    caption = models.TextField(null=True)
    description = models.TextField(null=True)
    source = models.ForeignKey('URL', related_name="fbpost.source", null=True)
    properties_raw = models.TextField(null=True) #not supported but saved
    icon = models.ForeignKey('URL', related_name="fbpost.icon", null=True)
    #actions = array of objects containing the name and link #will not be supported
    privacy_raw = models.TextField(null=True) #not supported but saved
    ftype = models.CharField(max_length=255, null=True)
    likes_from = models.ManyToManyField('FBUser', related_name='fbpost.likes_from', null=True)
    likes_count = models.IntegerField(null=True)
    comments_count = models.IntegerField(null=True)
    place_raw = models.TextField(null=True) #not supported but saved 
    story =  models.TextField(null=True)
    story_tags_raw = models.TextField(null=True) #not supported but saved 
    object_id = models.BigIntegerField(null=True)
    application_raw = models.TextField(null=True) #not supported but saved 
    created_time = models.DateTimeField(null=True)
    updated_time = models.DateTimeField(null=True)

    def update_from_facebook(self, facebook_model, user):
        model_changed = False
        props_to_check = {
                            u"fid":u"id",
                            u"message":u"message",
                            u"message_tags_raw":u"message_tags",
                            u"name":u"name",
                            u"caption":u"caption",
                            u"description":u"description",
                            u"properties_raw":u"properties",
                            u"privacy_raw":u"privacy",
                            u"ftype":u"type",
                            u"place_raw":u"place",
                            u"story":u"story",
                            u"story_tags_raw":u"story_tags",
                            u"object_id":u"object_id",
                            u"application_raw":u"application",
                            }

        subitem_to_check = {
                            u"likes_count":[u"likes",u"count"],
                            u"comments_count":[u"comments",u"count"],
                            }

        date_to_check = [u"created_time", u"updated_time"]

        self.user = user

        for prop in props_to_check:
            if props_to_check[prop] in facebook_model and self.__dict__[prop] != facebook_model[props_to_check[prop]]:
                self.__dict__[prop] = facebook_model[props_to_check[prop]]
                #print "prop changed:", prop
                model_changed = True

        for prop in subitem_to_check:
            subprop = subitem_to_check[prop]
            if subprop[0] in facebook_model and \
               subprop[1] in facebook_model[subprop[0]] and \
                self.__dict__[prop] != facebook_model[subprop[0]][subprop[1]]:

                self.__dict__[prop] = facebook_model[subprop[0]][subprop[1]]
                #print "prop changed:", prop
                model_changed = True

        for prop in date_to_check:
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(facebook_model[prop],'%Y-%m-%dT%H:%M:%S+0000'))
            #TODO implement cleaner time comparison
            if str(self.__dict__[prop]) != str(ts):
                self.__dict__[prop] = ts
                #print "prop changed:", prop
                model_changed = True

        if model_changed:
            self.model_update_date = datetime.now()
            self.save()
            #print "Status SAVED!", self

        return model_changed
        
class FBComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.text

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True, unique=True)
    ffrom = models.ForeignKey('FBUser')
    message = models.TextField(null=True)
    created_time = models.DateTimeField(null=True)
    likes = models.IntegerField(null=True)
    user_likes = models.IntegerField(null=True)
    ftype = models.CharField(max_length=255, null=True)
    post = models.ForeignKey('FBPost', null=True)












