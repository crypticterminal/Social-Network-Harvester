from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'SocialNetworkHarvester.views.home', name='home'),
    # url(r'^SocialNetworkHarvester/', include('SocialNetworkHarvester.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^fandjango/', include('fandjango.urls')),
    url(r'^$', include('snh.urls')),
)
