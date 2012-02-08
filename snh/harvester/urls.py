# coding=UTF-8

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('harvester.views',
    (r'^$', 'index'),
    (r'^(?P<user_id>\d+)/$', 'detail'),

)
