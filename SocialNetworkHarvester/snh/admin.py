from django.contrib import admin

from snh.models.twitter import TwitterHarvester
from snh.models.twitter import TWUser

from snh.models.facebook import FacebookHarvester
from snh.models.facebook import FBUser


class TwitterHarvesterInline(admin.StackedInline):
    model = TwitterHarvester.twusers_to_harvest.through
    extra = 1

class TwitterHarvesterAdmin(admin.ModelAdmin):
    fields = [
                'name', 
                'is_active', 
                'consumer_key',
                'consumer_secret',
                'access_token_key',
                'access_token_secret',
            ]

    inlines = [TwitterHarvesterInline]

class TWUserAdmin(admin.ModelAdmin):
    fields = [
                'screen_name', 
                'error_triggered', 
            ]

admin.site.register(TwitterHarvester, TwitterHarvesterAdmin)
admin.site.register(TWUser, TWUserAdmin)

class FacebookHarvesterInline(admin.StackedInline):
    model = FacebookHarvester.fbusers_to_harvest.through
    extra = 1

class FacebookHarvesterAdmin(admin.ModelAdmin):
    fields = [
                'name', 
                'is_active', 
            ]

    inlines = [FacebookHarvesterInline]

class FBUserAdmin(admin.ModelAdmin):
    fields = [
                'username', 
#                'error_triggered', 
            ]

admin.site.register(FacebookHarvester, FacebookHarvesterAdmin)
admin.site.register(FBUser, FBUserAdmin)

