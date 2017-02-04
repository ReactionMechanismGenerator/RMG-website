
from django.template import RequestContext
from django.shortcuts import render_to_response

def index(request):
    """
    The RMG regression tests homepage.
    """
    return render_to_response('regression_tests.html', context_instance=RequestContext(request))