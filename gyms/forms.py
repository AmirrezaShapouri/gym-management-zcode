from django import forms

from .models import GymSettings, GymSubscription, GymSubscriptionRequest


class GymSettingsForm(forms.ModelForm):
    class Meta:
        model = GymSettings
        fields = ('name', 'phone', 'address', 'description', 'logo', 'primary_color')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class GymSubscriptionRequestForm(forms.ModelForm):
    def __init__(self, *args, gym, **kwargs):
        super().__init__(*args, **kwargs)
        self.gym = gym
        self.fields['invoice_image'].required = True

    class Meta:
        model = GymSubscriptionRequest
        fields = ('sessions', 'invoice_image')
        widgets = {
            'sessions': forms.Select(attrs={'class': 'form-select'}),
            'invoice_image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp',
            }),
        }

    def save(self, commit=True):
        subscription = super().save(commit=False)
        subscription.price = GymSubscription.PLAN_PRICES[subscription.sessions]
        subscription.gym = self.gym
        if commit:
            subscription.save()
        return subscription