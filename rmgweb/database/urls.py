from django.conf.urls.defaults import *

urlpatterns = patterns('rmgweb.database',

    # Database homepage
    (r'^$', 'views.index'),

)
