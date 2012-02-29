# coding=UTF-8

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('snh.views',

    (r'^$', 'index'),
    (r'^reset_fb_token$', 'reset_fb_token'),
    (r'^request_fb_token$', 'request_fb_token'),
    (r'^test_fb_token$', 'test_fb_token'),

    (r'^twitter_detail/(?P<user_id>\d+)/$', 'twitter_detail'),
    (r'^twitter$', 'twitter'),

)
