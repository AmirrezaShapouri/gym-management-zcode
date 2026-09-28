from django import forms

from .models import GymSettings, GymSubscription


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
    class Meta:
        model = GymSubscription
        fields = ('sessions', 'invoice_image')
        widgets = {
            'sessions': forms.Select(attrs={'class': 'form-select'}),
            'invoice_image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invoice_image'].required = True

    def save(self, commit=True):
        subscription = super().save(commit=False)
        subscription.price = GymSubscription.PLAN_PRICES[subscription.sessions]
        subscription.status = GymSubscription.STATUS_PENDING
        subscription.start_date = None
        subscription.end_date = None
        if commit:
            subscription.save()
        return subscription