# coding=UTF-8

from django.db import models

# Create your models here.

class URL(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.original_url

    original_url = models.CharField(max_length=400,null=True)
    unshorten_url = models.CharField(max_length=400,null=True)
        
