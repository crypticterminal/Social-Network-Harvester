# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist

from fandjango.decorators import facebook_authorization_required
from fandjango.models import User as FanUser

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.dailymotionmodel import *
from snh.models.youtubemodel import *
from snh.utils import get_datatables_records

from django import template
from django.template.defaultfilters import stringfilter

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")

register = template.Library()
@register.filter
@stringfilter
def int_to_string(value):
    return value

@login_required(login_url=u'/login/')
def index(request):
    twitter_harvesters = TwitterHarvester.objects.all()
    facebook_harvesters = FacebookHarvester.objects.all()
    dailymotion_harvesters = DailyMotionHarvester.objects.all()
    youtube_harvesters = YoutubeHarvester.objects.all()

    return  render_to_response(u'snh/index.html',{
                                                    u'home_selected':True,
                                                    u'twitter_harvesters':twitter_harvesters,
                                                    u'facebook_harvesters':facebook_harvesters,
                                                    u'dailymotion_harvesters':dailymotion_harvesters,
                                                    u'youtube_harvesters':youtube_harvesters,
                                                  })

#
# TWITTER
#
@login_required(login_url=u'/login/')
def tw(request, harvester_id):
    twitter_harvesters = TwitterHarvester.objects.all()

    return  render_to_response(u'snh/twitter.html',{
                                                    u'tw_selected':True,
                                                    u'all_harvesters':twitter_harvesters,
                                                    u'harvester_id':harvester_id,
                                                  })

@login_required(login_url=u'/login/')
def tw_user_detail(request, harvester_id, screen_name):
    twitter_harvesters = TwitterHarvester.objects.all()
    user = get_list_or_404(TWUser, screen_name=screen_name)[0]
    return  render_to_response(u'snh/twitter_detail.html',{
                                                    u'tw_selected':True,
                                                    u'all_harvesters':twitter_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':user,
                                                  })
#
# TWITTER AJAX
#
@login_required(login_url=u'/login/')
def get_tw_list(request, harvester_id):
    querySet = None

    if harvester_id == "0":
        querySet = TWUser.objects.all()
    else:
        harvester = TwitterHarvester.objects.get(pmk_id__exact=harvester_id)
        querySet = harvester.twusers_to_harvest.all()

    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'name',
                            1 : u'screen_name',
                            2 : u'description',
                            3 : u'followers_count',
                            4 : u'friends_count',
                            5 : u'statuses_count',
                            6 : u'listed_count',
                            }
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap)

@login_required(login_url=u'/login/')
def get_twsearch_list(request, harvester_id):
    querySet = None

    if harvester_id == "0":
        querySet = TWSearch.objects.all()
    else:
        harvester = TwitterHarvester.objects.get(pmk_id__exact=harvester_id)
        querySet = harvester.twsearch_to_harvest.all()

    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'term',
                            }
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap)

#
# FACEBOOK TOKEN
#
@login_required(login_url=u'/login/')
@facebook_authorization_required
def request_fb_token(request):
    fanu = FanUser.objects.all()[0]
    userfb = None
    if fanu:
        userfb = fanu.graph.get(u"me")
    return  render_to_response(u'snh/test_token.html',{u'user': userfb})

@login_required(login_url=u'/login/')
def test_fb_token(request):
    fanu = FanUser.objects.all()[0]
    #userfb = None
    #if fanu:
    #    userfb = fanu.graph.get(u"me")
    #return  render_to_response(u'snh/test_token.html',{u'user': userfb, u'fanu':fanu})
    return  render_to_response(u'snh/test_token.html',{u'fanu':fanu})

#
# OLD VIEWS
#

#@login_required(login_url='/login/')
#def twitter(request, harvester_id):
#    if harvester_id == "0":
#        user_list = TWUser.objects.all()
#        search_list = TWSearch.objects.all()
#    else:
#        harvester = TwitterHarvester.objects.filter(pmk_id__exact=harvester_id)[0]
#        user_list = harvester.twusers_to_harvest.all()
#        search_list = harvester.twsearch_to_harvest.all()
#        
#    all_harvesters =  TwitterHarvester.objects.all()
#    return  render_to_response(u'snh/twitter.html',{u'user_list': user_list,"harvesters":all_harvesters,"searches":search_list})

#@login_required(login_url=u'/login/')
#def twitter_detail(request, screen_name):
#    user = get_object_or_404(TWUser, screen_name=screen_name)
#    statuses = TWStatus.objects.filter(user=user).order_by(u"created_at")
#    search_list = []
#    try:
#        search = TWSearch.objects.get(term__exact="@%s" % user.screen_name)
#        search_list = search.status_list.all()
#    except ObjectDoesNotExist:
#        pass
#    return render_to_response(u'snh/twitter_detail.html', {u'twuser': user, u'statuses':statuses,u"searches":search_list, u'len':len(statuses)})

#@login_required(login_url=u'/login/')
#def twitter_search_detail(request, search_pmkid):
#    search = get_object_or_404(TWSearch, pmk_id=search_pmkid)
#    statuses = search.status_list.all().order_by(u"created_at")
#    return render_to_response(u'snh/twitter_search_detail.html', {u'search': search, u'statuses':statuses, u'len':len(statuses)})

#@login_required(login_url=u'/login/')
#def twitter_status(request, status_id):
#    status = get_object_or_404(TWStatus, fid=status_id)
#    return render_to_response(u'snh/twitter_status.html', {u'twuser': status.user, 
#                                                           u'status':status, 
#                                                            u'mentions':status.user_mentions.all(),
#                                                            u'urls':status.text_urls.all(),
#                                                            u'tags':status.hash_tags.all(),
#                                                            })


#@login_required(login_url=u'/login/')
#def facebook(request, harvester_id):
#   if harvester_id == "0":
#        user_list = FBUser.objects.all()
#    else:
#        harvester = FacebookHarvester.objects.filter(pmk_id__exact=harvester_id)[0]
#        user_list = harvester.fbusers_to_harvest.all()
#    all_harvesters =  FacebookHarvester.objects.all()
#    return  render_to_response(u'snh/facebook.html',{u'user_list': user_list,"harvesters":all_harvesters})

#@login_required(login_url=u'/login/')
#def facebook_detail(request, user_id):
#    user = get_object_or_404(FBUser, fid=user_id)
#    posts = FBPost.objects.filter(user=user).order_by(u"created_time")
#    other_posts = FBPost.objects.filter(ffrom=user).exclude(user=user).order_by(u"created_time")
#    comments = FBComment.objects.filter(ffrom=user)
#    return render_to_response(u'snh/facebook_detail.html', {u'fbuser': user, 
#                                                            u'posts':posts, 
#                                                            u'other_posts':other_posts, 
#                                                            u'comments':comments, 
#                                                            u'len':len(posts),
#                                                            u'len_comments':len(comments),
#                                                            u'len_other_posts':len(other_posts),
#                                                            })

#@login_required(login_url=u'/login/')
#def facebook_post(request, post_id):
#    post = get_object_or_404(FBPost, fid=post_id)
#    comments = FBComment.objects.filter(post=post)
#    likes_user = post.likes_from.all()
#    return render_to_response(u'snh/facebook_post.html', {u'fbuser': post.user, 
#                                                            u'post':post, 
#                                                            u'likes_user':likes_user, 
#                                                            u'comments':comments,
#                                                            })



#def logout_view(request):
#    logout(request)

#@login_required(login_url=u'/login/')
#def reset_fb_token(request):
#    user = FanUser.objects.all().delete()
#    return  redirect(u"snh.views.request_fb_token")

#@login_required(login_url=u'/login/')
#@facebook_authorization_required
#def request_fb_token(request):
#    fanu = FanUser.objects.all()[0]
#    userfb = None
#    if fanu:
#        userfb = fanu.graph.get(u"me")
#    return  render_to_response(u'snh/test_token.html',{u'user': userfb})

#@login_required(login_url=u'/login/')
#def test_fb_token(request):
#    fanu = FanUser.objects.all()[0]
#    userfb = None
#    if fanu:
#        userfb = fanu.graph.get(u"me")
#    return  render_to_response(u'snh/test_token.html',{u'user': userfb})

