# coding=UTF-8

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('snh.views',
    (r'^request_fb_token$', 'request_fb_token'),
    (r'^test_fb_token$', 'test_fb_token'),

    (r'^$', 'index'),
    (r'^tw/(?P<harvester_id>\d+)$', 'tw'),
    (r'^get_tw_list/(?P<harvester_id>\d+)/$', 'get_tw_list'),
    (r'^get_twsearch_list/(?P<harvester_id>\d+)/$', 'get_twsearch_list'),
    (r'^tw_user_detail/(?P<harvester_id>\d+)/(?P<screen_name>\w+)/$', 'tw_user_detail'),

    #(r'^$', 'index'),
    #(r'^reset_fb_token$', 'reset_fb_token'),
    #(r'^request_fb_token$', 'request_fb_token'),
    #(r'^test_fb_token$', 'test_fb_token'),

    #(r'^twitter_status/(?P<status_id>\d+)/$', 'twitter_status'),
    #(r'^twitter_search_detail/(?P<search_pmkid>\w+)/$', 'twitter_search_detail'),
    #(r'^twitter/(?P<harvester_id>\d+)/$', 'twitter'),

    #(r'^facebook_post/(?P<post_id>\w+)/$', 'facebook_post'),
    #(r'^facebook_detail/(?P<user_id>\d+)/$', 'facebook_detail'),
    #(r'^facebook/(?P<harvester_id>\d+)/$', 'facebook'),

)
