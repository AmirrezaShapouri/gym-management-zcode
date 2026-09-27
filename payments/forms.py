from django import forms

from members.models import Subscription
from .models import Expense, Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ('member', 'subscription', 'amount', 'plan_label', 'method', 'status', 'reference', 'date', 'note')
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'subscription': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'plan_label': forms.TextInput(attrs={'class': 'form-control'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['subscription'].required = False

    def clean(self):
        cleaned_data = super().clean()
        subscription = cleaned_data.get('subscription')
        member = cleaned_data.get('member')
        if subscription and member and subscription.member_id != member.pk:
            self.add_error('subscription', 'اشتراک انتخاب‌شده متعلق به این عضو نیست.')
        return cleaned_data


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ('member', 'plan', 'sessions', 'price', 'start_date', 'end_date', 'status')
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'sessions': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('start_date', 'end_date'):
            self.fields[field_name].input_formats = ['%Y-%m-%d']

    def clean(self):
        cleaned_data = super().clean()
        plan = cleaned_data.get('plan')
        sessions = cleaned_data.get('sessions')
        if plan and sessions and plan.sessions != sessions:
            self.add_error('sessions', 'تعداد جلسات باید با پلن انتخاب‌شده یکسان باشد.')
        return cleaned_data


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('title', 'category', 'vendor', 'amount', 'date', 'status', 'method', 'reference', 'note')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'vendor': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'method': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%Y-%m-%d']