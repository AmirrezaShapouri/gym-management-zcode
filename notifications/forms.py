from django import forms

from classes.models import GymClass
from .models import Announcement, SMSSettings


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('message_type', 'body', 'classes')
        widgets = {
            'message_type': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'classes': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
        }

    def __init__(self, *args, gym, **kwargs):
        super().__init__(*args, **kwargs)
        self.gym = gym
        self.fields['classes'].queryset = GymClass.objects.filter(gym=gym, is_active=True).order_by('name')

    def save(self, commit=True):
        announcement = super().save(commit=False)
        announcement.gym = self.gym
        if commit:
            announcement.save()
            self.save_m2m()
        return announcement


class SMSSettingsForm(forms.ModelForm):
    class Meta:
        model = SMSSettings
        fields = ('enabled', 'expiry_sms', 'payment_sms', 'registration_sms', 'reminder_sms')
        widgets = {
            field: forms.CheckboxInput(attrs={'class': 'form-check-input'})
            for field in fields
        }