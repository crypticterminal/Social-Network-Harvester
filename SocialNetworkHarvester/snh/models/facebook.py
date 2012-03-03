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
        return self.username
   
    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True)
    name = models.CharField(max_length=255, null=True)
    #petite entorse. username n'existe pas pour les fanpages. dans ce cas name==username
    username = models.CharField(max_length=255, null=True)
    website = models.ForeignKey('URL', related_name="fbuser.website", null=True)
    link = models.ForeignKey('URL', related_name="fbuser.link", null=True)

    user_desc = models.ForeignKey('FBUserDesc', related_name="fbuser.user_desc", null=True)
    page_desc = models.ForeignKey('FBPageDesc', related_name="fbuser.page_desc", null=True)

    error_triggered = models.BooleanField()

    def update_from_facebook(self,fb_user):
        model_changed = False
        props_to_check = {
                            "fid":"id",
                            "name":"name",
                            "username":"username",
                            }

        for prop in props_to_check:
            if props_to_check[prop] in fb_user and self.__dict__[prop] != fb_user[props_to_check[prop]]:
                self.__dict__[prop] = fb_user[props_to_check[prop]]
                print "prop changed:", prop
                model_changed = True

        if model_changed:
            self.model_update_date = datetime.now()
            self.save()
            print "User SAVED!", self

class FBUserDesc(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.username

    pmk_id =  models.AutoField(primary_key=True)

    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    gender = models.CharField(max_length=255, null=True)
    locale = models.CharField(max_length=255, null=True)
    #languages = {"id":id, "name":name}
    third_party_id = models.CharField(max_length=255, null=True)
    #installed = {"type":user, "id":id, "installed":true|None}
    #timezone = number
    updated_time = models.DateTimeField(null=True)
    verified = models.BooleanField()
    bio = models.TextField(null=True)
    birthday = models.DateTimeField(null=True)
    #education = array of objects containing year and type fields, and school object (name, id, type, and optional year, degree, concentration array, classes array, and with array )
    email = models.CharField(max_length=255, null=True)
    hometown = models.CharField(max_length=255, null=True)
    #interested_in = array containing strings
    #location = object containing name and id
    political = models.TextField(null=True)
    #favorite_athletes = array of objects containing id and name fields
    #favorite_tames = array of objects containing id and name fields
    quotes = models.TextField(max_length=255, null=True)
    relationship_status = models.TextField(null=True)
    religion = models.TextField(null=True)
    #significant_other = object containing name and id
    #video_upload_limits = object containing length and size of video

    #work = array of objects containing employer, location, position, start_date and end_date fields       

class FBPageDesc(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.username

    pmk_id =  models.AutoField(primary_key=True)

    #fid = models.CharField(max_length=255, null=True)
    #name = models.CharField(max_length=255, null=True)
    #link = models.ForeignKey('URL', related_name="fbpage.link", null=True)
    #website = models.ForeignKey('URL', related_name="fbpage.website", null=True)

    category = models.TextField(null=True)
    likes = models.IntegerField(null=True)
    #location = dictionnary
    phone = models.CharField(max_length=255, null=True)
    checkins = models.IntegerField(null=True)
    picture = models.ForeignKey('URL', related_name="fbpagedesc.picture", null=True)
    talking_about_count = models.IntegerField(null=True)

class FBPost(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.ftype

    pmk_id =  models.AutoField(primary_key=True)
    user = models.ForeignKey('FBUser')

    fid = models.CharField(max_length=255, null=True)
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
    object_id = models.IntegerField(null=True)
    application_raw = models.TextField(null=True) #not supported but saved 
    created_time = models.DateTimeField(null=True)
    updated_time = models.DateTimeField(null=True)

    def update_from_facebook(self, facebook_model, user):
        model_changed = False
        props_to_check = {
                            "fid":"id",
                            "message":"message",
                            "message_tags_raw":"message_tags",
                            "name":"name",
                            "caption":"caption",
                            "description":"description",
                            "properties_raw":"properties",
                            "privacy_raw":"privacy",
                            "ftype":"type",
                            "place_raw":"place",
                            "story":"story",
                            "story_tags_raw":"story_tags",
                            "object_id":"object_id",
                            "application_raw":"application",
                            }

        subitem_to_check = {
                            "likes_count":["likes","count"],
                            "comments_count":["comments","count"],
                            }

        date_to_check = ["created_time", "updated_time"]

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

        
class FBComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.text

    pmk_id =  models.AutoField(primary_key=True)

    fid = models.CharField(max_length=255, null=True)
    ffrom = models.ForeignKey('FBUser')
    message = models.TextField(null=True)
    created_time = models.DateTimeField(null=True)
    likes = models.IntegerField(null=True)
    user_likes = models.IntegerField(null=True)
    ftype = models.CharField(max_length=255, null=True)
    post = models.ForeignKey('FBPost', null=True)












