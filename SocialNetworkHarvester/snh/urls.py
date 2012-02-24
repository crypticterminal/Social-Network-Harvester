# coding=UTF-8

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('snh.views',

    url(r'^fandjango/', include('fandjango.urls')),
    (r'^$', 'index'),

)
