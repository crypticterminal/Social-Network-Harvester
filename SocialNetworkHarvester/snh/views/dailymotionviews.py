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
# DAILYMOTION
#
@login_required(login_url=u'/login/')
def dm(request, harvester_id):
    dailymotion_harvesters = DailyMotionHarvester.objects.all()
    return  render_to_response(u'snh/dailymotion.html',{
                                                    u'dm_selected':True,
                                                    u'all_harvesters':dailymotion_harvesters,
                                                    u'harvester_id':harvester_id,
                                                  })

#
# DailyMotion AJAX
#
@login_required(login_url=u'/login/')
def get_dm_list(request, harvester_id):
    querySet = None

    if harvester_id == "0":
        querySet = DMUser.objects.all()
    else:
        harvester = DailyMotionHarvester.objects.get(pmk_id__exact=harvester_id)
        querySet = harvester.dmusers_to_harvest.all()

    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'fid',
                            1 : u'username',
                            2 : u'screenname',
                            3 : u'gender',
                            4 : u'description',
                            5 : u'language',
                            6 : u'status',
                            7 : u'ftype',
                            8 : u'url__original_url',
                            }
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap)

### OLD VIEWS

##
## FACEBOOK
##
#@login_required(login_url=u'/login/')
#def fb(request, harvester_id):
#    facebook_harvesters = FacebookHarvester.objects.all()
#
#    return  render_to_response(u'snh/facebook.html',{
#                                                    u'fb_selected':True,
#                                                    u'all_harvesters':facebook_harvesters,
#                                                    u'harvester_id':harvester_id,
#                                                  })
#
#@login_required(login_url=u'/login/')
#def fb_user_detail(request, harvester_id, username):
#    facebook_harvesters = FacebookHarvester.objects.all()
#    user = get_list_or_404(FBUser, username=username)[0]
#    return  render_to_response(u'snh/facebook_detail.html',{
#                                                    u'fb_selected':True,
#                                                    u'all_harvesters':facebook_harvesters,
#                                                    u'harvester_id':harvester_id,
#                                                    u'user':user,
#                                                  })
#@login_required(login_url=u'/login/')
#def fb_userfid_detail(request, harvester_id, userfid):
#    facebook_harvesters = FacebookHarvester.objects.all()
#    user = get_list_or_404(FBUser, fid=userfid)[0]
#    return  render_to_response(u'snh/facebook_detail.html',{
#                                                    u'fb_selected':True,
#                                                    u'all_harvesters':facebook_harvesters,
#                                                    u'harvester_id':harvester_id,
#                                                    u'user':user,
#                                                  })
#
#@login_required(login_url=u'/login/')
#def fb_post_detail(request, harvester_id, post_id):
#    facebook_harvesters = FacebookHarvester.objects.all()
#    post = get_object_or_404(FBPost, fid=post_id)
#    return  render_to_response(u'snh/facebook_post.html',{
#                                                    u'fb_selected':True,
#                                                    u'all_harvesters':facebook_harvesters,
#                                                    u'harvester_id':harvester_id,
#                                                    u'user':post.user,
#                                                    u'post':post,
#                                                  })
#
##
## Facebook AJAX
##
#@login_required(login_url=u'/login/')
#def get_fb_list(request, harvester_id):
#    querySet = None
#
#    if harvester_id == "0":
#        querySet = FBUser.objects.all()
#    else:
#        harvester = FacebookHarvester.objects.get(pmk_id__exact=harvester_id)
#        querySet = harvester.fbusers_to_harvest.all()
#
#    #columnIndexNameMap is required for correct sorting behavior
#    columnIndexNameMap = {
#                            0 : u'fid',
#                            1 : u'name',
#                            2 : u'username',
#                            3 : u'category',
#                            4 : u'likes',
#                            5 : u'about',
#                            6 : u'phone',
#                            7 : u'checkins',
#                            8 : u'talking_about_count',
#                            }
#    #call to generic function from utils
#    return get_datatables_records(request, querySet, columnIndexNameMap)
#
#@login_required(login_url=u'/login/')
#def get_fb_post_list(request, username):
#    querySet = None
#    #columnIndexNameMap is required for correct sorting behavior
#
#    columnIndexNameMap = {
#                            0 : u'created_time',
#                            1 : u'fid',
#                            2 : u'ffrom__username',
#                            3 : u'name',
#                            4 : u'description',
#                            5 : u'caption',
#                            6 : u'message',
#                            7 : u'link__original_url',
#                            8 : u'ftype',
#                            9 : u'likes_count',
#                            10: u'shares_count',
#                            11: u'comments_count',
#                            12: u'application_raw',
#                            13: u'updated_time',
#                            14: u'story',
#                            15: u'ffrom__name',
#                            16: u'ffrom__fid',
#                            }
#    try:
#        user = get_list_or_404(FBUser, username=username)[0]
#        querySet = FBPost.objects.filter(user=user)
#    except ObjectDoesNotExist:
#        pass
#    #call to generic function from utils
#    return get_datatables_records(request, querySet, columnIndexNameMap)
#
#@login_required(login_url=u'/login/')
#def get_fb_otherpost_list(request, userfid):
#    querySet = None
#    #columnIndexNameMap is required for correct sorting behavior
#
#    columnIndexNameMap = {
#                            0 : u'created_time',
#                            1 : u'fid',
#                            2 : u'user__username',
#                            3 : u'name',
#                            4 : u'description',
#                            5 : u'caption',
#                            6 : u'message',
#                            7 : u'link__original_url',
#                            8 : u'ftype',
#                            9 : u'likes_count',
#                            10: u'shares_count',
#                            11: u'comments_count',
#                            12: u'application_raw',
#                            13: u'updated_time',
#                            14: u'story',
#                            15: u'user__name',
#                            16: u'user__fid',
#                            }
#    try:
#        user = get_list_or_404(FBUser, fid=userfid)[0]
#        querySet = FBPost.objects.filter(ffrom=user).exclude(user=user).order_by(u"created_time")
#    except ObjectDoesNotExist:
#        pass
#    #call to generic function from utils
#    return get_datatables_records(request, querySet, columnIndexNameMap)
#
#@login_required(login_url=u'/login/')
#def get_fb_comment_list(request, userfid):
#    querySet = None
#    #columnIndexNameMap is required for correct sorting behavior
#
#    columnIndexNameMap = {
#                            0 : u'created_time',
#                            1 : u'ffrom__username',
#                            2 : u'post__ffrom__name',
#                            3 : u'post__fid',
#                            4 : u'message',
#                            5 : u'likes',
#                            6: u'user_likes',
#                            7: u'ftype',
#                            8: u'ffrom__name',
#                            9: u'ffrom__fid',
#                            10: u'post__ffrom__fid',
#                            }
#    try:
#        user = get_list_or_404(FBUser, fid=userfid)[0]
#        querySet = FBComment.objects.filter(ffrom=user)
#    except ObjectDoesNotExist:
#        pass
#    #call to generic function from utils
#    return get_datatables_records(request, querySet, columnIndexNameMap)
#
#@login_required(login_url=u'/login/')
#def get_fb_postcomment_list(request, postfid):
#    querySet = None
#    #columnIndexNameMap is required for correct sorting behavior
#
#    columnIndexNameMap = {
#                            0 : u'created_time',
#                            1 : u'ffrom__username',
#                            2 : u'message',
#                            3 : u'likes',
#                            4: u'user_likes',
#                            5: u'ftype',
#                            6: u'ffrom__name',
#                            7: u'ffrom__fid',
#                            8: u'post__fid',
#                            }
#    try:
#        post = get_list_or_404(FBPost, fid=postfid)[0]
#        querySet = FBComment.objects.filter(post=post)
#    except ObjectDoesNotExist:
#        pass
#    #call to generic function from utils
#    return get_datatables_records(request, querySet, columnIndexNameMap)
#
#@login_required(login_url=u'/login/')
#def get_fb_likes_list(request, postfid):
#    querySet = None
#    #columnIndexNameMap is required for correct sorting behavior
#
#    columnIndexNameMap = {
#                            0 : u'fid',
#                            1 : u'name',
#                            }
#    try:
#        post = get_list_or_404(FBPost, fid=postfid)[0]
#        querySet = post.likes_from.all()
#    except ObjectDoesNotExist:
#        pass
#    #call to generic function from utils
#    return get_datatables_records(request, querySet, columnIndexNameMap)
#
