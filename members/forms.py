from django import forms

from classes.models import Coach, GymClass
from .models import Member


class MemberForm(forms.ModelForm):
    def __init__(self, *args, gym, **kwargs):
        super().__init__(*args, **kwargs)
        self.gym = gym
        self.fields['gym_class'].queryset = GymClass.objects.filter(gym=gym)
        self.fields['coach'].queryset = Coach.objects.filter(gym=gym)

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

    def save(self, commit=True):
        member = super().save(commit=False)
        member.gym = self.gym
        if commit:
            member.save()
            self.save_m2m()
        return member