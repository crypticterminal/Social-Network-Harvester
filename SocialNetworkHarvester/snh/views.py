# coding=UTF-8

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
#from fandjango.decorators import facebook_authorization_required
#from django.http import HttpResponse
#from fandjango.models import User as FanUser

def index(request):
    return  render_to_response('snh/index.html',{'user_list': ''})
