# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect
from fandjango.decorators import facebook_authorization_required
from fandjango.models import User as FanUser

from snh.models.twitter import *
from snh.models.facebook import *

@login_required(login_url='/login/')
def index(request):
    return  render_to_response('snh/index.html',{'user_list': ''})

@login_required(login_url='/login/')
def twitter(request):
    user_list = TWUser.objects.all()
    return  render_to_response('snh/twitter.html',{'user_list': user_list})

@login_required(login_url='/login/')
def twitter_detail(request, user_id):
    user = get_object_or_404(TWUser, fid=user_id)
    statuses = TWStatus.objects.filter(user=user).order_by("-created_at")
    return render_to_response('snh/twitter_detail.html', {'user': user, 'statuses':statuses})

@login_required(login_url='/login/')
def facebook(request):
    user_list = FBUser.objects.all()
    return  render_to_response('snh/facebook.html',{'user_list': user_list})

@login_required(login_url='/login/')
def facebook_detail(request, user_id):
    user = get_object_or_404(FBUser, fid=user_id)
    posts = FBPost.objects.filter(user=user).order_by("-created_time")
    return render_to_response('snh/facebook_detail.html', {'user': user, 'posts':posts})

def logout_view(request):
    logout(request)

@login_required(login_url='/login/')
def reset_fb_token(request):
    user = FanUser.objects.all().delete()
    return  redirect("snh.views.request_fb_token")

@login_required(login_url='/login/')
@facebook_authorization_required
def request_fb_token(request):
    fanu = get_list_or_404("FanUser")
    userfb = None
    if fanu:
        userfb = fanu[0].user.graph.get("me")
    return  render_to_response('snh/test_token.html',{'user': userfb})

@login_required(login_url='/login/')
def test_fb_token(request):
    fanu = get_list_or_404("FanUser")
    userfb = None
    if fanu:
        userfb = fanu[0].user.graph.get("me")
    return  render_to_response('snh/test_token.html',{'user': userfb})

