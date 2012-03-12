# coding=UTF-8

from django.contrib import admin

from snh.models.twittermodel import TwitterHarvester
from snh.models.twittermodel import TWUser

from snh.models.facebookmodel import FacebookHarvester
from snh.models.facebookmodel import FBUser


class TwitterHarvesterInline(admin.StackedInline):
    model = TwitterHarvester.twusers_to_harvest.through
    extra = 1

class TwitterHarvesterAdmin(admin.ModelAdmin):
    fields = [
                u'harvester_name', 
                u'is_active', 
                u'consumer_key',
                u'consumer_secret',
                u'access_token_key',
                u'access_token_secret',
                u'dont_harvest_further_than',
                u'full_harvest_on_next_run',
            ]

    inlines = [TwitterHarvesterInline]

class TWUserAdmin(admin.ModelAdmin):
    fields = [
                u'screen_name', 
                u'error_triggered', 
            ]

admin.site.register(TwitterHarvester, TwitterHarvesterAdmin)
admin.site.register(TWUser, TWUserAdmin)

class FacebookHarvesterInline(admin.StackedInline):
    model = FacebookHarvester.fbusers_to_harvest.through
    extra = 1

class FacebookHarvesterAdmin(admin.ModelAdmin):
    fields = [
                u'harvester_name', 
                u'is_active', 
            ]

    inlines = [FacebookHarvesterInline]

class FBUserAdmin(admin.ModelAdmin):
    fields = [
                u'username', 
                u'error_triggered', 
            ]

admin.site.register(FacebookHarvester, FacebookHarvesterAdmin)
admin.site.register(FBUser, FBUserAdmin)

