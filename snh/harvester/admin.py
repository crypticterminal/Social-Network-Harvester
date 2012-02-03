from harvester.models.twitter import Harvester
from django.contrib import admin

class HarvesterInline(admin.StackedInline):
    model = Harvester.users_to_harvest.through
    extra = 1

class HarvesterAdmin(admin.ModelAdmin):
    fields = [
                'name', 
                'consumer_key',
                'consumer_secret',
                'access_token_key',
                'access_token_secret',
            ]

    inlines = [HarvesterInline]

admin.site.register(Harvester, HarvesterAdmin)




