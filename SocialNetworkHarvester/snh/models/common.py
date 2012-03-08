# coding=UTF-8

from datetime import datetime
from django.db import models


class AbstractHaverster(models.Model):

    class Meta:
        app_label = "snh"
        asbtract = True

    def __unicode__(self):
        return u"%s/%s" % (unicode(self.harvester_type),unicode(self.harvester_name))

    harvester_type = models.CharField(max_length=255, null=True)
    harvester_name = models.CharField(max_length=255, null=True)

    last_harvest_call_count = models.BigIntegerField(null=True, unique=True)
    current_harvest_call_count = models.BigIntegerField(null=True, unique=True)

    is_active = models.BooleanField()
    harvest_in_progress =  models.BooleanField()
    last_user_harvest_was_aborted =  models.BooleanField()
    retry_user_after_abortion =  models.BooleanField()

    last_harvest_start_time = models.DateTimeField(null=True)
    last_harvest_end_time = models.DateTimeField(null=True)

    current_harvest_start_time = models.DateTimeField(null=True)

    def start_new_harvest(self):
        self.current_harvest_start_time = datetime.now()
        self.current_harvest_call_count = 0
        self.harvest_in_progress = True
        self.save()

    def ending_current_harvest(self):
        self.last_harvest_start_time = self.current_harvest_start_time
        self.last_harvest_end_time = datetime.now()
        self.current_harvest_start_time = None
        self.last_harvest_call_count = self.current_harvest_call_count
        self.last_user_harvest_was_aborted = bool(self.get_last_harvested_user())
        self.save()

    def api_call(self, method, params):
        self.current_harvest_call_count = self.current_harvest_call_count + 1
        self.save()

    def get_last_harvested_user(self, params):
        raise NotImplementedError( "Should have implemented this" )

    def get_current_harvested_user(self, params):
        raise NotImplementedError( "Should have implemented this" )

    def get_next_user_to_harvest(self):
        raise NotImplementedError( "Should have implemented this" )

    def get_stats(self):
        return {"abstract":
                    {
                    "harvester_type":harvester_type,
                    "harvester_name":harvester_name,

                    "last_harvest_call_count":last_harvest_call_count,
                    "current_harvest_call_count":current_harvest_call_count,

                    "is_active":is_active,
                    "harvest_in_progress":harvest_in_progress,

                    "last_harvest_start_time":last_harvest_start_time,
                    "last_harvest_end_time":last_harvest_end_time,

                    "current_harvest_start_time":current_harvest_start_time,
                    },
                "concrete":{},
                }

class URL(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.original_url

    original_url = models.TextField(null=True)
    unshorten_url = models.TextField(null=True)
    last_snapshot_time = models.DateTimeField(null=True)

class Image(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.name

    name = models.TextField(null=True)
