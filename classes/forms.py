from django import forms
from django.forms import inlineformset_factory

from core.jalali import WEEKDAY_KEYS
from .models import Coach
from .models import ClassPlan, GymClass


class GymClassForm(forms.ModelForm):
    days = forms.MultipleChoiceField(
        label='روزهای برگزاری',
        choices=WEEKDAY_KEYS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = GymClass
        fields = ('name', 'coach', 'days', 'start_time', 'end_time', 'capacity', 'is_active', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'coach': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, gym, **kwargs):
        super().__init__(*args, **kwargs)
        self.gym = gym
        self.fields['coach'].queryset = Coach.objects.filter(gym=gym)
        if self.instance and self.instance.pk and not self.is_bound:
            self.initial['days'] = self.instance.days_list

    def clean_days(self):
        return ' '.join(self.cleaned_data['days'])

    def save(self, commit=True):
        gym_class = super().save(commit=False)
        gym_class.gym = self.gym
        if commit:
            gym_class.save()
            self.save_m2m()
        return gym_class


ClassPlanFormSet = inlineformset_factory(
    GymClass,
    ClassPlan,
    fields=('sessions', 'price'),
    extra=1,
    can_delete=True,
    widgets={
        'sessions': forms.Select(attrs={'class': 'form-select'}),
        'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
    },
)