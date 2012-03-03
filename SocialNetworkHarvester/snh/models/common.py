# coding=UTF-8

from django.db import models

# Create your models here.

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
