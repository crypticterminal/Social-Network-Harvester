# coding=UTF-8

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('snh.views',

    (r'^$', 'index'),
    (r'^reset_fb_token$', 'reset_fb_token'),
    (r'^request_fb_token$', 'request_fb_token'),
    (r'^test_fb_token$', 'test_fb_token'),

    (r'^twitter_status/(?P<status_id>\d+)/$', 'twitter_status'),
    (r'^twitter_detail/(?P<screen_name>\w+)/$', 'twitter_detail'),
    (r'^twitter_search_detail/(?P<search_pmkid>\w+)/$', 'twitter_search_detail'),
    (r'^twitter/(?P<harvester_id>\d+)/$', 'twitter'),

    (r'^facebook_post/(?P<post_id>\w+)/$', 'facebook_post'),
    (r'^facebook_detail/(?P<user_id>\d+)/$', 'facebook_detail'),
    (r'^facebook/(?P<harvester_id>\d+)/$', 'facebook'),

)
