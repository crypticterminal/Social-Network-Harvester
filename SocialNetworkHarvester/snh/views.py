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
    facebook_harvesters = FacebookHarvester.objects.all()

    return  render_to_response(u'snh/index.html',{u'twitter_harvesters':twitter_harvesters,'facebook_harvesters':facebook_harvesters})

@login_required(login_url='/login/')
def twitter(request, harvester_id):
    if harvester_id == "0":
        user_list = TWUser.objects.all()
    else:
        harvester = TwitterHarvester.objects.filter(pmk_id__exact=harvester_id)[0]
        user_list = harvester.twusers_to_harvest.all()
    all_harvesters =  TwitterHarvester.objects.all()
    return  render_to_response(u'snh/twitter.html',{u'user_list': user_list,"harvesters":all_harvesters})

@login_required(login_url=u'/login/')
def twitter_detail(request, user_id):
    user = get_object_or_404(TWUser, fid=user_id)
    statuses = TWStatus.objects.filter(user=user).order_by(u"created_at")
    return render_to_response(u'snh/twitter_detail.html', {u'twuser': user, u'statuses':statuses, u'len':len(statuses)})

@login_required(login_url=u'/login/')
def twitter_status(request, status_id):
    status = get_object_or_404(TWStatus, fid=status_id)
    return render_to_response(u'snh/twitter_status.html', {u'twuser': status.user, 
                                                            u'status':status, 
                                                            u'mentions':status.user_mentions.all(),
                                                            u'urls':status.text_urls.all(),
                                                            u'tags':status.hash_tags.all(),
                                                            })



@login_required(login_url=u'/login/')
def facebook(request, harvester_id):
    if harvester_id == "0":
        user_list = FBUser.objects.all()
    else:
        harvester = FacebookHarvester.objects.filter(pmk_id__exact=harvester_id)[0]
        user_list = harvester.fbusers_to_harvest.all()
    all_harvesters =  FacebookHarvester.objects.all()
    return  render_to_response(u'snh/facebook.html',{u'user_list': user_list,"harvesters":all_harvesters})

@login_required(login_url=u'/login/')
def facebook_detail(request, user_id):
    user = get_object_or_404(FBUser, fid=user_id)
    posts = FBPost.objects.filter(user=user).order_by(u"created_time")
    other_posts = FBPost.objects.filter(ffrom=user).exclude(user=user).order_by(u"created_time")
    comments = FBComment.objects.filter(ffrom=user)
    return render_to_response(u'snh/facebook_detail.html', {u'fbuser': user, 
                                                            u'posts':posts, 
                                                            u'other_posts':other_posts, 
                                                            u'comments':comments, 
                                                            u'len':len(posts),
                                                            u'len_comments':len(comments),
                                                            u'len_other_posts':len(other_posts),
                                                            })

@login_required(login_url=u'/login/')
def facebook_post(request, post_id):
    post = get_object_or_404(FBPost, fid=post_id)
    comments = FBComment.objects.filter(post=post)
    return render_to_response(u'snh/facebook_post.html', {u'fbuser': post.user, 
                                                            u'post':post, 
                                                            u'comments':comments,
                                                            })



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

