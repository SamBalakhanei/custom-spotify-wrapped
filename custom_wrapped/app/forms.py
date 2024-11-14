from django.db import transaction
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

input_classes = 'shadow appearance-none border rounded-lg w-full p-2 py-2 px-3 leading-tight focus:outline-none focus:shadow-outline'

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email']
        
    
    email = forms.EmailField(required=True,
                             label='Email',
                             widget=forms.EmailInput(attrs={'placeholder': 'Email',
                                                            'class': input_classes}))
    
    username = forms.CharField(required=True,
                               label='Username',
                               widget=forms.TextInput(attrs={'placeholder': 'Username',
                                                             'class': input_classes}))

    password1 = forms.CharField(
        required=True,
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password',
                                          'class': input_classes})
    )
    password2 = forms.CharField(
        required=True,
        label='Retype password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Retype password',
                                          'class': input_classes})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("An account with this username already exists.")
        return username

    def save(self, commit=True):
        # Only save the user if form is valid
        with transaction.atomic():
            if not self.is_valid():
                raise ValueError("Form is not valid. Cannot save user.")
            
            user = super().save(commit=False)
            user.email = self.cleaned_data["email"]
            user.username = self.cleaned_data["username"]
            user.set_password(self.cleaned_data["password1"])
            
            if commit:
                user.save()
        return user
    
        
class CustomLoginForm(AuthenticationForm):            
    username = forms.CharField(required=True,
                            label='Username',
                            widget=forms.TextInput(attrs={'placeholder' :'Username',
                                                        'class': input_classes}))

    password = forms.CharField(
        required=True,
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder' :'Password',
                                          'class': input_classes}))
