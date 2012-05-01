# coding=UTF-8

from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models

from snh.models.twittermodel import TwitterHarvester
from snh.models.twittermodel import TWUser, TWSearch

from snh.models.facebookmodel import FacebookHarvester
from snh.models.facebookmodel import FBUser

from snh.models.dailymotionmodel import DailyMotionHarvester
from snh.models.dailymotionmodel import DMUser

from snh.models.youtubemodel import YoutubeHarvester
from snh.models.youtubemodel import YTUser
#############
class TwitterHarvesterAdmin(admin.ModelAdmin):
    #fields = [
    #            u'harvester_name', 
    #            u'is_active', 
    #            u'twusers_to_harvest',
    #            u'twsearch_to_harvest',
    #            u'consumer_key',
    #            u'consumer_secret',
    #            u'access_token_key',
    #            u'access_token_secret',
    #            u'max_retry_on_fail',
    #            u'harvest_window_from',
    #            u'harvest_window_to',#

    #        ]

    fieldsets = (
        ('', {
            'fields': (
                            u'harvester_name', 
                            u'is_active', 
                            u'consumer_key',
                            u'consumer_secret',
                            u'access_token_key',
                            u'access_token_secret',
                            u'max_retry_on_fail',
                            u'harvest_window_from',
                            u'harvest_window_to',
                        ),
        }),
        ('Users to harvest', {
            'classes': ('collapse open',),
            'fields' : ('twusers_to_harvest',),
        }),
        ('Searches to harvest', {
            'classes': ('collapse open',),
            'fields' : ('twsearch_to_harvest',),
        }),
    )
    #formfield_overrides = {
        #models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        #models.ManyToManyField: {'widget': FilteredSelectMultiple("Item",False)},
    #}
    # define the raw_id_fields
    raw_id_fields = ('twusers_to_harvest','twsearch_to_harvest',)
    # define the related_lookup_fields
    related_lookup_fields = {
        'm2m': ['twusers_to_harvest','twsearch_to_harvest',],
    }

class TWUserAdmin(admin.ModelAdmin):
    fields = [
                u'screen_name', 
                u'error_triggered', 
            ]

class TWSearchAdmin(admin.ModelAdmin):
    fields = [
                u'term', 
            ]

admin.site.register(TwitterHarvester, TwitterHarvesterAdmin)
admin.site.register(TWUser, TWUserAdmin)
admin.site.register(TWSearch, TWSearchAdmin)

##############
class FacebookHarvesterAdmin(admin.ModelAdmin):
    fields = [
                u'harvester_name', 
                u'is_active',
                u'fbusers_to_harvest',
                u'update_likes',
                u'max_retry_on_fail',
                u'harvest_window_from',
                u'harvest_window_to',
            ]

    formfield_overrides = {
        #models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.ManyToManyField: {'widget': FilteredSelectMultiple("Item",False)},
    }

class FBUserAdmin(admin.ModelAdmin):
    fields = [
                u'username', 
                u'error_triggered', 
            ]

admin.site.register(FacebookHarvester, FacebookHarvesterAdmin)
admin.site.register(FBUser, FBUserAdmin)

##############
class DailyMotionHarvesterAdmin(admin.ModelAdmin):
    fields = [
                u'harvester_name', 
                u'key', 
                u'secret', 
                u'user', 
                u'password', 
                u'is_active',
                u'dmusers_to_harvest',
                u'max_retry_on_fail',
                u'harvest_window_from',
                u'harvest_window_to',
            ]

    formfield_overrides = {
        #models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.ManyToManyField: {'widget': FilteredSelectMultiple("Item",False)},
    }

class DMUserAdmin(admin.ModelAdmin):
    fields = [
                u'username',
            ]

admin.site.register(DailyMotionHarvester, DailyMotionHarvesterAdmin)
admin.site.register(DMUser, DMUserAdmin)

##############
class YoutubeHarvesterAdmin(admin.ModelAdmin):
    fields = [
                u'harvester_name', 
                u'dev_key', 
                u'is_active',
                u'ytusers_to_harvest',
                u'max_retry_on_fail',
                u'harvest_window_from',
                u'harvest_window_to',
            ]

    formfield_overrides = {
        #models.CharField: {'widget': TextInput(attrs={'size':'20'})},
        models.ManyToManyField: {'widget': FilteredSelectMultiple("Item",False)},
    }

class YTUserAdmin(admin.ModelAdmin):
    fields = [
                u'username', 
            ]

admin.site.register(YoutubeHarvester, YoutubeHarvesterAdmin)
admin.site.register(YTUser, YTUserAdmin)

