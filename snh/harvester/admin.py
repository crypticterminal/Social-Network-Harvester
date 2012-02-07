from harvester.models.twitter import Harvester
from harvester.models.twitter import User
from harvester.models.twitter import Status
from django.contrib import admin

class HarvesterInline(admin.StackedInline):
    model = Harvester.users_to_harvest.through
    extra = 1

class HarvesterAdmin(admin.ModelAdmin):
    fields = [
                'name', 
                'is_active', 
                'consumer_key',
                'consumer_secret',
                'access_token_key',
                'access_token_secret',
            ]

    inlines = [HarvesterInline]

admin.site.register(Harvester, HarvesterAdmin)
admin.site.register(User)
admin.site.register(Status)



