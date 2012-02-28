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

    name = models.CharField(max_length=200, null=True)

    user = models.ForeignKey('FBUser', null=True)
    
    access_token = models.CharField(max_length=200, null=True)
    app_id = models.CharField(max_length=200, null=True)
    app_secret = models.CharField(max_length=200, null=True)

    is_active = models.BooleanField()

    fbusers_to_harvest = models.ManyToManyField('FBUser', related_name='fbusers_to_harvest')

class FBUser(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.username

    oid = models.CharField(max_length=200, null=True)
    name = models.CharField(max_length=200, null=True)
    #petite entorse. username n'existe pas pour les fanpages. dans ce cas name==username
    username = models.CharField(max_length=200, null=True)
    websited = models.ForeignKey('URL', related_name="fbuser.website", null=True)
    link = models.ForeignKey('URL', related_name="fbuser.link", null=True)

    user_desc = models.ForeignKey('FBUserDesc', related_name="fbuser.user_desc", null=True)
    page_desc = models.ForeignKey('FBPageDesc', related_name="fbuser.page_desc", null=True)


class FBUserDesc(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.username

    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True)
    gender = models.CharField(max_length=200, null=True)
    locale = models.CharField(max_length=200, null=True)
    #languages = {"id":id, "name":name}
    third_party_id = models.CharField(max_length=200, null=True)
    #installed = {"type":user, "id":id, "installed":true|None}
    #timezone = number
    updated_time = models.DateTimeField(null=True)
    verified = models.BooleanField()
    bio = models.CharField(max_length=1024, null=True)
    birthday = models.DateTimeField(null=True)
    #education = array of objects containing year and type fields, and school object (name, id, type, and optional year, degree, concentration array, classes array, and with array )
    email = models.CharField(max_length=200, null=True)
    hometown = models.CharField(max_length=200, null=True)
    #interested_in = array containing strings
    #location = object containing name and id
    political = models.CharField(max_length=200, null=True)
    #favorite_athletes = array of objects containing id and name fields
    #favorite_tames = array of objects containing id and name fields
    quotes = models.CharField(max_length=200, null=True)
    relationship_status = models.CharField(max_length=200, null=True)
    religion = models.CharField(max_length=200, null=True)
    #significant_other = object containing name and id
    #video_upload_limits = object containing length and size of video

    #work = array of objects containing employer, location, position, start_date and end_date fields       

class FBPageDesc(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.username

    #oid = models.CharField(max_length=200, null=True)
    #name = models.CharField(max_length=200, null=True)
    #link = models.ForeignKey('URL', related_name="fbpage.link", null=True)
    #website = models.ForeignKey('URL', related_name="fbpage.website", null=True)

    category = models.CharField(max_length=200, null=True)
    likes = models.IntegerField(null=True)
    #location = dictionnary
    phone = models.CharField(max_length=200, null=True)
    checkins = models.IntegerField(null=True)
    picture = models.ForeignKey('URL', related_name="fbpagedesc.picture", null=True)
    talking_about_count = models.IntegerField(null=True)

class FBPost(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.text

    user = models.ForeignKey('FBUser')

    oid = models.CharField(max_length=200, null=True)
    user = models.ForeignKey('FBUser')
    #to = Contains in data an array of objects, each with the name and Facebook id of the user
    to = models.ManyToManyField('FBUser', related_name='fbpost.to')
    message = models.CharField(max_length=4*1024, null=True)
    #message_tags = object containing fields whose names are the indexes to where objects are mentioned in the message field; each field in turn is an array containing an object with id, name, offset, and length fields, where length is the length, within the message field, of the object mentioned
    picture = models.ForeignKey('URL', related_name="fbpost.picture", null=True)
    link = models.ForeignKey('URL', related_name="fbpost.link", null=True)
    name = models.CharField(max_length=200, null=True)
    caption = models.CharField(max_length=200, null=True)
    description = models.CharField(max_length=200, null=True)
    source = models.ForeignKey('URL', related_name="fbpost.source", null=True)
    #properties = array of objects containing the name and text
    icon = models.ForeignKey('URL', related_name="fbpost.icon", null=True)
    #actions = array of objects containing the name and link
    #privacy = voir doc
    otype = models.CharField(max_length=200, null=True)
    #likes = Structure containing a data object and the count of total likes, with data containing an array of objects, each with the name and Facebook id of the user who liked the post
    likes_from = models.ManyToManyField('FBUser', related_name='fbpost.likes_from')
    likes_count = models.IntegerField(null=True)
    #place = object containing id and name of Page associated with this location, and a location field containing geographic information such as latitude, longitude, country, and other fields (fields will vary based on geography and availability of information)
    story =  models.CharField(max_length=200, null=True)
    #story_tags = object containing fields whose names are the indexes to where objects are mentioned in the message field; each field in turn is an array containing an object with id, name, offset, and length fields, where length is the length, within the message field, of the object mentioned
    #comments = Structure containing a data object containing an array of objects, each with the id, from, message, and created_time for each comment
    object_id = models.IntegerField(null=True)
    #application = object containing the name and id of the application
    created_time = models.DateTimeField(null=True)
    updated_time = models.DateTimeField(null=True)
        
class FBComment(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.text

    oid = models.CharField(max_length=200, null=True)
    user = models.ForeignKey('FBUser')
    message = models.CharField(max_length=4*1024, null=True)
    created_time = models.DateTimeField(null=True)
    likes = models.IntegerField(null=True)
    post = models.ForeignKey('FBPost', null=True)














