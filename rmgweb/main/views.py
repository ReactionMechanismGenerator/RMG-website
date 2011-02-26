from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
import django.contrib.auth.views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from forms import UserProfileForm

def index(request):
    """
    The RMG website homepage.
    """
    return render_to_response('index.html', context_instance=RequestContext(request))

def login(request):
    """
    Called when the user wishes to log in to his/her account.
    """
    return django.contrib.auth.views.login(request, template_name='login.html')

def logout(request):
    """
    Called when the user wishes to log out of his/her account.
    """
    return django.contrib.auth.views.logout(request, template_name='logout.html')

def viewProfile(request, username):
    """
    Called when the user wishes to view another user's profile. The other user
    is identified by his/her `username`. Note that viewing user profiles does
    not require authentication.
    """
    user0 = User.objects.get(username=username)
    return render_to_response('viewProfile.html', {'user0': user0}, context_instance=RequestContext(request))

@login_required
def editProfile(request):
    """
    Called when the user wishes to edit his/her user profile.
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/') # Redirect after POST
    else:
        form = UserProfileForm(instance=request.user) # An unbound form

    return render_to_response('editProfile.html', {'form': form}, context_instance=RequestContext(request))
    