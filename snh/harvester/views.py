from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from harvester.models.twitter import *

def index(request):
    
    user_list = User.objects.all()
    return  render_to_response('harvester/index.html',{'user_list': user_list})

def detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    statuses = get_list_or_404(Status.objects.order_by('-created_at'), user=user)
    return render_to_response('harvester/detail.html', {'user': user, 'statuses':statuses})
