from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User

from .models import Profile


class ProfileForm(forms.ModelForm):
    phone = forms.CharField(label='شماره تماس', required=False, max_length=20)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, profile, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        if not self.is_bound:
            self.initial['phone'] = profile.phone

    def save(self, commit=True):
        user = super().save(commit=commit)
        self.profile.phone = self.cleaned_data['phone']
        if commit:
            self.profile.save(update_fields=['phone'])
        return user


class StaffUserForm(forms.ModelForm):
    password = forms.CharField(label='گذرواژه', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label='شماره همراه', max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(
        label='نقش',
        choices=(
            (Profile.ROLE_MANAGER, 'مدیر'),
            (Profile.ROLE_RECEPTION, 'پذیرش'),
            (Profile.ROLE_COACH, 'مربی'),
        ),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, gym, **kwargs):
        super().__init__(*args, **kwargs)
        self.gym = gym

    def clean_password(self):
        password = self.cleaned_data['password']
        password_validation.validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            user.profile.role = self.cleaned_data['role']
            user.profile.phone = self.cleaned_data['phone']
            user.profile.gym = self.gym
            user.profile.save(update_fields=['role', 'phone', 'gym'])
        return user