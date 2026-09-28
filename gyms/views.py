from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.mixins import role_required
from .forms import GymSettingsForm
from .models import GymSettings


@role_required('manager')
@require_http_methods(['GET', 'POST'])
def settings(request):
	gym = GymSettings.load()
	form = GymSettingsForm(request.POST or None, request.FILES or None, instance=gym)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'تنظیمات باشگاه ذخیره شد.')
		return redirect('gym_settings')
	return render(request, 'gyms/settings.html', {'gym': gym, 'form': form})
