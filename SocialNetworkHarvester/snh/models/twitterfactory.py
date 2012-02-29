# coding=UTF-8

from django.db import models
from django.db.models import Q
from snh.models.twitter import *

def get_user(screen_name=None, twitter_id=None):
    print "s%s id%s" %(screen_name, twitter_id)
    user = User.objects.get(Q(screen_name__exact=screen_name))
    print user

