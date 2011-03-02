from django.conf.urls.defaults import *

urlpatterns = patterns('rmgweb.database',

    # Database homepage
    (r'^$', 'views.index'),

    # Thermodynamics database
    (r'^thermo/$', 'views.thermo'),
    (r'^thermo/(?P<section>\w+)/$', 'views.thermo'),
    (r'^thermo/(?P<section>\w+)/(?P<subsection>\w+)/$', 'views.thermo'),
    (r'^thermo/(?P<section>\w+)/(?P<subsection>\w+)/(?P<index>\d+).html$', 'views.thermoEntry'),

)
