# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect
from fandjango.decorators import facebook_authorization_required
from fandjango.models import User as FanUser

from snh.models.twitter import *
from snh.models.facebook import *

@login_required(login_url=u'/login/')
def index(request):
    return  render_to_response(u'snh/index.html',{u'user_list': ''})

@login_required(login_url='/login/')
def twitter(request):
    user_list = TWUser.objects.all()
    return  render_to_response(u'snh/twitter.html',{u'user_list': user_list})

@login_required(login_url=u'/login/')
def twitter_detail(request, user_id):
    user = get_object_or_404(TWUser, fid=user_id)
    statuses = TWStatus.objects.filter(user=user).order_by(u"-created_at")
    return render_to_response(u'snh/twitter_detail.html', {u'user': user, u'statuses':statuses})

@login_required(login_url=u'/login/')
def facebook(request):
    user_list = FBUser.objects.all()
    return  render_to_response(u'snh/facebook.html',{u'user_list': user_list})

@login_required(login_url=u'/login/')
def facebook_detail(request, user_id):
    user = get_object_or_404(FBUser, fid=user_id)
    posts = FBPost.objects.filter(user=user).order_by(u"-created_time")
    return render_to_response(u'snh/facebook_detail.html', {u'user': user, u'posts':posts})

def logout_view(request):
    logout(request)

@login_required(login_url=u'/login/')
def reset_fb_token(request):
    user = FanUser.objects.all().delete()
    return  redirect(u"snh.views.request_fb_token")

@login_required(login_url=u'/login/')
@facebook_authorization_required
def request_fb_token(request):
    fanu = get_list_or_404(u"FanUser")
    userfb = None
    if fanu:
        userfb = fanu[0].user.graph.get(u"me")
    return  render_to_response(u'snh/test_token.html',{u'user': userfb})

@login_required(login_url=u'/login/')
def test_fb_token(request):
    fanu = get_list_or_404(u"FanUser")
    userfb = None
    if fanu:
        userfb = fanu[0].user.graph.get(u"me")
    return  render_to_response(u'snh/test_token.html',{u'user': userfb})

