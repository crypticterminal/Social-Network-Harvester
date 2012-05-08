# coding=UTF-8

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('snh.views',

    #ROOT
    (r'^$', 'index'),

    #TWITTER
    (r'^tw/(?P<harvester_id>\d+)$', 'tw'),
    (r'^tw_user_detail/(?P<harvester_id>\d+)/(?P<screen_name>\w+)/$', 'tw_user_detail'),
    (r'^tw_search_detail/(?P<harvester_id>\d+)/(?P<search_id>\d+)/$', 'tw_search_detail'),
    (r'^tw_status_detail/(?P<harvester_id>\d+)/(?P<status_id>\d+)/$', 'tw_status_detail'),
    #TWITTER AJAX
    (r'^get_tw_list/(?P<harvester_id>\d+)/$', 'get_tw_list'),
    (r'^get_twsearch_list/(?P<harvester_id>\d+)/$', 'get_twsearch_list'),
    (r'^get_tw_status_list/(?P<screen_name>\w+)/$', 'get_tw_status_list'),
    (r'^get_tw_statussearch_list/(?P<screen_name>\w+)/$', 'get_tw_statussearch_list'),
    (r'^get_tw_searchdetail_list/(?P<search_id>\d+)/$', 'get_tw_searchdetail_list'),

    #FACEBOOK
    (r'^request_fb_token$', 'request_fb_token'),
    (r'^test_fb_token$', 'test_fb_token'),
    (r'^fb/(?P<harvester_id>\d+)$', 'fb'),
    (r'^fb_user_detail/(?P<harvester_id>\d+)/(?P<username>[\w\.]+)/$', 'fb_user_detail'),
    (r'^fb_user_detail/(?P<harvester_id>\d+)/fid/(?P<userfid>[\w\.]+)/$', 'fb_userfid_detail'),
    (r'^fb_post_detail/(?P<harvester_id>\d+)/(?P<post_id>[\w\.]+)/$', 'fb_post_detail'),
    #FACEBOOK AJAX
    (r'^get_fb_list/(?P<harvester_id>\d+)/$', 'get_fb_list'),
    (r'^get_fb_post_list/(?P<username>[\w\.]+)/$', 'get_fb_post_list'),
    (r'^get_fb_otherpost_list/(?P<userfid>[\w\.]+)/$', 'get_fb_otherpost_list'),
    (r'^get_fb_comment_list/(?P<userfid>[\w\.]+)/$', 'get_fb_comment_list'),
    (r'^get_fb_postcomment_list/(?P<postfid>[\w\.]+)/$', 'get_fb_postcomment_list'),
    (r'^get_fb_likes_list/(?P<postfid>[\w\.]+)/$', 'get_fb_likes_list'),

    #DAILYMOTION
    (r'^dm/(?P<harvester_id>\d+)$', 'dm'),
    #DAILYMOTION AJAX
    (r'^get_dm_list/(?P<harvester_id>\d+)/$', 'get_dm_list'),

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
