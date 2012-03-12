# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect
from fandjango.decorators import facebook_authorization_required
from fandjango.models import User as FanUser

from snh.models.twittermodel import *
from snh.models.facebookmodel import *

@login_required(login_url=u'/login/')
def index(request):

    twitter_harvesters = TwitterHarvester.objects.all()
    tw_stats = []
    for th in twitter_harvesters:
        tw_stats += th.get_stats()["abstract"]

    facebook_harvesters = FacebookHarvester.objects.all()
    fb_stats = []
    for fb in facebook_harvesters:
        fb_stats += fb.get_stats()

    return  render_to_response(u'snh/index.html',{u'tw_stats':tw_stats,'fb_stats':fb_stats})

@login_required(login_url='/login/')
def twitter(request):
    user_list = TWUser.objects.all()
    return  render_to_response(u'snh/twitter.html',{u'user_list': user_list,u'twitter':True})

@login_required(login_url=u'/login/')
def twitter_detail(request, user_id):
    user = get_object_or_404(TWUser, fid=user_id)
    statuses = TWStatus.objects.filter(user=user).order_by(u"-created_at")
    return render_to_response(u'snh/twitter_detail.html', {u'twuser': user, u'statuses':statuses, u'len':len(statuses),u'twitter':True})

@login_required(login_url=u'/login/')
def facebook(request):
    user_list = FBUser.objects.all()
    return  render_to_response(u'snh/facebook.html',{u'user_list': user_list})

@login_required(login_url=u'/login/')
def facebook_detail(request, user_id):
    user = get_object_or_404(FBUser, fid=user_id)
    posts = FBPost.objects.filter(user=user).order_by(u"-created_time")
    return render_to_response(u'snh/facebook_detail.html', {u'fbuser': user, u'posts':posts, u'len':len(posts)})

def logout_view(request):
    logout(request)

@login_required(login_url=u'/login/')
def reset_fb_token(request):
    user = FanUser.objects.all().delete()
    return  redirect(u"snh.views.request_fb_token")

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
    userfb = None
    if fanu:
        userfb = fanu.graph.get(u"me")
    return  render_to_response(u'snh/test_token.html',{u'user': userfb})

