from django import forms

from models import UserProfile

class UserProfileForm(forms.ModelForm):
    """
    A form for editing user profile information.
    """
    class Meta:
        model = UserProfile
        exclude = ('user')
    
    username = forms.CharField(label="Username", widget=forms.TextInput(attrs={'readonly':'readonly'}))
    first_name = forms.CharField(label="First Name", max_length=30)
    last_name = forms.CharField(label="Last Name", max_length=30)
    email = forms.CharField(label="Email", max_length=50)
    
