# coding=UTF-8

from django.contrib import admin

from snh.models.twittermodel import TwitterHarvester
from snh.models.twittermodel import TWUser

from snh.models.facebookmodel import FacebookHarvester
from snh.models.facebookmodel import FBUser

from snh.models.dailymotionmodel import DailyMotionHarvester
from snh.models.dailymotionmodel import DMUser

from snh.models.youtubemodel import YoutubeHarvester
from snh.models.youtubemodel import YTUser
#############
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
                u'max_retry_on_fail',
                u'harvest_window_from',
                u'harvest_window_to',

            ]

    inlines = [TwitterHarvesterInline]

class TWUserAdmin(admin.ModelAdmin):
    fields = [
                u'screen_name', 
                u'error_triggered', 
            ]

admin.site.register(TwitterHarvester, TwitterHarvesterAdmin)
admin.site.register(TWUser, TWUserAdmin)

##############
class FacebookHarvesterInline(admin.StackedInline):
    model = FacebookHarvester.fbusers_to_harvest.through
    extra = 1

class FacebookHarvesterAdmin(admin.ModelAdmin):
    fields = [
                u'harvester_name', 
                u'is_active',
                u'max_retry_on_fail',
                u'harvest_window_from',
                u'harvest_window_to',
            ]

    inlines = [FacebookHarvesterInline]

class FBUserAdmin(admin.ModelAdmin):
    fields = [
                u'username', 
                u'error_triggered', 
            ]

admin.site.register(FacebookHarvester, FacebookHarvesterAdmin)
admin.site.register(FBUser, FBUserAdmin)

##############
class DailyMotionHarvesterInline(admin.StackedInline):
    model = DailyMotionHarvester.dmusers_to_harvest.through
    extra = 1

class DailyMotionHarvesterAdmin(admin.ModelAdmin):
    fields = [
                u'harvester_name', 
                u'key', 
                u'secret', 
                u'user', 
                u'password', 
                u'is_active',
                u'max_retry_on_fail',
                u'harvest_window_from',
                u'harvest_window_to',
            ]

    inlines = [DailyMotionHarvesterInline]

class DMUserAdmin(admin.ModelAdmin):
    fields = [
                u'screenname', 
            ]

admin.site.register(DailyMotionHarvester, DailyMotionHarvesterAdmin)
admin.site.register(DMUser, DMUserAdmin)

##############
class YoutubeHarvesterInline(admin.StackedInline):
    model = YoutubeHarvester.ytusers_to_harvest.through
    extra = 1

class YoutubeHarvesterAdmin(admin.ModelAdmin):
    fields = [
                u'harvester_name', 
                u'dev_key', 
                u'is_active',
                u'max_retry_on_fail',
                u'harvest_window_from',
                u'harvest_window_to',
            ]

    inlines = [YoutubeHarvesterInline]

class YTUserAdmin(admin.ModelAdmin):
    fields = [
                u'username', 
            ]

admin.site.register(YoutubeHarvester, YoutubeHarvesterAdmin)
admin.site.register(YTUser, YTUserAdmin)

