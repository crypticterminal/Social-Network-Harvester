# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect
from fandjango.decorators import facebook_authorization_required
from fandjango.models import User as FanUser
#from django.http import HttpResponse

@login_required(login_url='/login/')
def index(request):
    return  render_to_response('snh/index.html',{'user_list': ''})

def logout_view(request):
    logout(request)

def reset_fb_token(request):
    user = FanUser.objects.all().delete()
    return  redirect("snh.views.request_fb_token")

@facebook_authorization_required
def request_fb_token(request):
    fanu = get_list_or_404("FanUser")
    userfb = None
    if fanu:
        userfb = fanu[0].user.graph.get("me")
    return  render_to_response('snh/test_token.html',{'user': userfb})

def test_fb_token(request):
    fanu = get_list_or_404("FanUser")
    userfb = None
    if fanu:
        userfb = fanu[0].user.graph.get("me")
    return  render_to_response('snh/test_token.html',{'user': userfb})

