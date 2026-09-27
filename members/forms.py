from django import forms

from .models import Member


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ('first_name', 'last_name', 'phone', 'gender', 'gym_class', 'coach')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'tel'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'gym_class': forms.Select(attrs={'class': 'form-select'}),
            'coach': forms.Select(attrs={'class': 'form-select'}),
        }