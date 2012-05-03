# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django import template
from django.template.defaultfilters import stringfilter

from fandjango.decorators import facebook_authorization_required
from fandjango.models import User as FanUser

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from snh.models.dailymotionmodel import *

from snh.utils import get_datatables_records

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")

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
# FACEBOOK
#
@login_required(login_url=u'/login/')
def fb(request, harvester_id):
    facebook_harvesters = FacebookHarvester.objects.all()

    return  render_to_response(u'snh/facebook.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                  })

@login_required(login_url=u'/login/')
def fb_user_detail(request, harvester_id, username):
    facebook_harvesters = FacebookHarvester.objects.all()
    user = get_list_or_404(FBUser, username=username)[0]
    return  render_to_response(u'snh/facebook_detail.html',{
                                                    u'fb_selected':True,
                                                    u'all_harvesters':facebook_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':user,
                                                  })
#
# Facebook AJAX
#
@login_required(login_url=u'/login/')
def get_fb_list(request, harvester_id):
    querySet = None

    if harvester_id == "0":
        querySet = FBUser.objects.all()
    else:
        harvester = FacebookHarvester.objects.get(pmk_id__exact=harvester_id)
        querySet = harvester.fbusers_to_harvest.all()

    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'fid',
                            1 : u'name',
                            2 : u'username',
                            3 : u'category',
                            4 : u'likes',
                            5 : u'about',
                            6 : u'phone',
                            7 : u'checkins',
                            8 : u'talking_about_count',
                            }
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap)

@login_required(login_url=u'/login/')
def get_fb_post_list(request, username):
    querySet = None
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'created_time',
                            1 : u'fid',
                            2 : u'name',
                            3 : u'description',
                            4 : u'story',
                            5 : u'message',
                            6 : u'caption',
                            7 : u'link__original_url',
                            8 : u'ftype',
                            9 : u'likes_count',
                            10: u'shares_count',
                            11: u'comments_count',
                            }
    try:
        user = get_list_or_404(FBUser, username=username)[0]
        querySet = FBPost.objects.filter(ffrom=user)
    except ObjectDoesNotExist:
        pass
    logger.info("#%s" % username)
    logger.info("#%s" % querySet.count())
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap)

#
# OLD VIEWS
#

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
