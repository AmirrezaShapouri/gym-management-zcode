from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from classes.models import GymClass
from core.mixins import portal_user_required
from members.models import Member
from .forms import AnnouncementForm, SMSSettingsForm
from .models import (
	Announcement,
	MemberNotificationSetting,
	SMSMessage,
	SMSSettings,
)


@portal_user_required
@require_http_methods(['GET', 'POST'])
def notification_list(request):
	form = AnnouncementForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		with transaction.atomic():
			announcement = form.save(commit=False)
			announcement.created_by = request.user
			announcement.save()
			form.save_m2m()
			recipients = Member.objects.filter(gym_class__in=announcement.classes.all()).distinct()
			SMSMessage.objects.bulk_create([
				SMSMessage(
					member=member,
					message_type=SMSMessage.TYPE_ANNOUNCEMENT,
					body=announcement.body,
					status=SMSMessage.STATUS_PENDING,
				)
				for member in recipients
			])
		messages.success(request, 'اعلانیه ثبت شد؛ پیامک‌ها در صف ارسال قرار گرفتند.')
		return redirect('notification_list')
	return render(request, 'notifications/notification_list.html', {
		'form': form,
		'announcements': Announcement.objects.prefetch_related('classes').all(),
		'messages_log': SMSMessage.objects.select_related('member').all(),
		'classes': GymClass.objects.select_related('coach').filter(is_active=True),
	})


@portal_user_required
@require_http_methods(['GET', 'POST'])
def notification_settings(request):
	settings_obj = SMSSettings.objects.first() or SMSSettings()
	settings_form = SMSSettingsForm(
		request.POST if request.method == 'POST' and 'save_global' in request.POST else None,
		instance=settings_obj,
	)
	members = Member.objects.select_related('gym_class').prefetch_related('subscriptions').order_by(
		'last_name', 'first_name'
	)
	if request.method == 'POST' and 'save_global' in request.POST and settings_form.is_valid():
		settings_form.save()
		messages.success(request, 'تنظیمات پیامک ذخیره شد.')
		return redirect('notification_settings')
	if request.method == 'POST' and 'save_members' in request.POST:
		with transaction.atomic():
			for member in members:
				prefix = f'member_{member.pk}_'
				MemberNotificationSetting.objects.update_or_create(
					member=member,
					defaults={
						'class_reminder': prefix + 'class_reminder' in request.POST,
						'subscription_expiry': prefix + 'subscription_expiry' in request.POST,
						'payment': prefix + 'payment' in request.POST,
						'registration': prefix + 'registration' in request.POST,
					},
				)
		messages.success(request, 'ترجیحات اعضا ذخیره شد.')
		return redirect('notification_settings')
	member_settings = {
		item.member_id: item
		for item in MemberNotificationSetting.objects.filter(member__in=members)
	}
	member_rows = []
	for member in members:
		setting = member_settings.get(member.pk)
		member_rows.append({
			'member': member,
			'class_reminder': setting.class_reminder if setting else True,
			'subscription_expiry': setting.subscription_expiry if setting else True,
			'payment': setting.payment if setting else True,
			'registration': setting.registration if setting else True,
		})
	return render(request, 'notifications/notification_settings.html', {
		'settings_form': settings_form,
		'settings_obj': settings_obj,
		'member_rows': member_rows,
	})
