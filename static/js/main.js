document.addEventListener('DOMContentLoaded', function () {
    // ---------- ابزارهای مشترک ----------
    function formatCurrency(value) {
        return Number(value).toLocaleString('fa-IR');
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>'"]/g, function (character) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[character];
        });
    }

    function normalizeDigits(value) {
        return String(value).replace(/[۰-۹]/g, function (digit) {
            return String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit));
        });
    }

    function faDigits(value) {
        return String(value).replace(/[0-9]/g, function (digit) {
            return '۰۱۲۳۴۵۶۷۸۹'[digit];
        });
    }

    function statusBadgeClass(status) {
        if (status === 'موفق' || status === 'پرداخت‌شده') {
            return 'bg-success';
        }
        if (status === 'ناموفق') {
            return 'bg-danger';
        }
        return 'bg-warning';
    }

    function addDeleteHandler(button, row) {
        button.addEventListener('click', function () {
            if (window.confirm('آیا از حذف این رکورد مطمئن هستید؟')) {
                row.remove();
            }
        });
    }

    // تبدیل تاریخ میلادی به شمسی (الگوریتم استاندارد جلالی)
    function toJalali(gy, gm, gd) {
        const gDaysInMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
        let jy = gy <= 1600 ? 0 : 979;
        gy -= gy <= 1600 ? 621 : 1600;
        const gy2 = gm > 2 ? gy + 1 : gy;
        let days = 365 * gy + Math.floor((gy2 + 3) / 4) - Math.floor((gy2 + 99) / 100)
            + Math.floor((gy2 + 399) / 400) - 80 + gd + gDaysInMonth[gm - 1];
        jy += 33 * Math.floor(days / 12053);
        days %= 12053;
        jy += 4 * Math.floor(days / 1461);
        days %= 1461;
        if (days > 365) {
            jy += Math.floor((days - 1) / 365);
            days = (days - 1) % 365;
        }
        const jm = days < 186 ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30);
        const jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);
        return [jy, jm, jd];
    }

    function todayJalali() {
        const now = new Date();
        const parts = toJalali(now.getFullYear(), now.getMonth() + 1, now.getDate());
        return parts[0] + '/' + String(parts[1]).padStart(2, '0') + '/' + String(parts[2]).padStart(2, '0');
    }

    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = 'alert alert-' + (type || 'success') + ' alert-dismissible fade show toast-alert';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = escapeHtml(message)
            + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
        document.body.appendChild(toast);
        setTimeout(function () {
            toast.classList.remove('show');
            setTimeout(function () { toast.remove(); }, 400);
        }, 4000);
    }

    // ---------- صفحه‌بندی سمت کاربر ----------
    const paginationControllers = [];

    function refreshPaginations() {
        paginationControllers.forEach(function (refresh) {
            refresh();
        });
    }

    document.querySelectorAll('.pagination').forEach(function (pagination) {
        const container = pagination.closest('.card');
        const table = container ? container.querySelector('table') : null;
        if (!table) return;

        const previousItem = pagination.querySelector('.page-item:first-child');
        const nextItem = pagination.querySelector('.page-item:last-child');
        const previousLink = previousItem ? previousItem.querySelector('.page-link') : null;
        const nextLink = nextItem ? nextItem.querySelector('.page-link') : null;
        const pageItems = Array.from(pagination.querySelectorAll('.page-item')).slice(1, -1);
        const pageSize = 5;
        let currentPage = 1;

        function getRows() {
            return Array.from(table.querySelectorAll('tbody > tr'))
                .filter(function (row) {
                    return row.dataset.filteredOut !== 'true';
                });
        }

        function renderPagination() {
            const rows = getRows();
            const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
            currentPage = Math.min(currentPage, pageCount);

            pageItems.forEach(function (item, index) {
                item.hidden = index + 1 > pageCount;
                const link = item.querySelector('.page-link');
                if (link) {
                    link.textContent = (index + 1).toLocaleString('fa-IR');
                    link.setAttribute('aria-current', index + 1 === currentPage ? 'page' : 'false');
                }
                item.classList.toggle('active', index + 1 === currentPage);
            });

            if (previousItem) previousItem.classList.toggle('disabled', currentPage === 1);
            if (nextItem) nextItem.classList.toggle('disabled', currentPage === pageCount);
            if (previousLink) previousLink.setAttribute('aria-disabled', currentPage === 1 ? 'true' : 'false');
            if (nextLink) nextLink.setAttribute('aria-disabled', currentPage === pageCount ? 'true' : 'false');

            table.querySelectorAll('tbody > tr').forEach(function (row) {
                const rowIndex = rows.indexOf(row);
                row.hidden = row.dataset.filteredOut === 'true'
                    || rowIndex < (currentPage - 1) * pageSize
                    || rowIndex >= currentPage * pageSize;
            });
        }

        pageItems.forEach(function (item, index) {
            const link = item.querySelector('.page-link');
            if (link) {
                link.addEventListener('click', function (event) {
                    event.preventDefault();
                    currentPage = index + 1;
                    renderPagination();
                });
            }
        });

        if (previousLink) {
            previousLink.addEventListener('click', function (event) {
                event.preventDefault();
                if (currentPage > 1) {
                    currentPage -= 1;
                    renderPagination();
                }
            });
        }

        if (nextLink) {
            nextLink.addEventListener('click', function (event) {
                event.preventDefault();
                const pageCount = Math.max(1, Math.ceil(getRows().length / pageSize));
                if (currentPage < pageCount) {
                    currentPage += 1;
                    renderPagination();
                }
            });
        }

        paginationControllers.push(renderPagination);
        renderPagination();
    });

    // ---------- منوی موبایل ----------
    const navbarToggler = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('#sidebar');

    if (navbarToggler && sidebar) {
        navbarToggler.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }

    // ---------- حذف خودکار هشدارهای ثابت ----------
    document.querySelectorAll('.alert:not(.toast-alert)').forEach(function (alert) {
        setTimeout(function () {
            alert.classList.add('fade');
            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // ---------- مودال تأیید حذف (لیست اعضا و کلاس‌ها) ----------
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        let pendingDeleteRow = null;

        document.querySelectorAll('[data-bs-target="#deleteModal"]').forEach(function (button) {
            button.addEventListener('click', function () {
                pendingDeleteRow = this.closest('tr');
            });
        });

        const confirmDeleteBtn = deleteModal.querySelector('.modal-footer .btn-danger');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', function () {
                if (pendingDeleteRow) {
                    pendingDeleteRow.remove();
                }
                pendingDeleteRow = null;
                const instance = bootstrap.Modal.getInstance(deleteModal);
                if (instance) {
                    instance.hide();
                }
                showToast('رکورد موردنظر حذف شد.', 'danger');
            });
        }
    }

    // ---------- فیلترهای لیست اعضا ----------
    const searchInput = document.getElementById('searchInput');
    const filterStatus = document.getElementById('filterStatus');
    const filterSubscription = document.getElementById('filterSubscription');
    const memberTable = document.getElementById('memberTable');

    if (memberTable && (searchInput || filterStatus || filterSubscription)) {
        function filterMembers() {
            const rawValue = searchInput ? searchInput.value.trim().toLowerCase() : '';
            const searchValue = rawValue || faDigits(rawValue).toLowerCase();
            const statusValue = filterStatus ? filterStatus.value : '';
            const subscriptionValue = filterSubscription ? filterSubscription.value : '';

            memberTable.querySelectorAll('tbody tr').forEach(function (row) {
                const name = row.cells[0].textContent.toLowerCase();
                const phone = row.cells[1].textContent.toLowerCase();
                const matchesSearch = !searchValue || name.includes(searchValue) || phone.includes(rawValue) || phone.includes(searchValue);
                const matchesStatus = !statusValue || row.cells[6].textContent.trim() === statusValue;
                const matchesSubscription = !subscriptionValue || row.cells[4].textContent.includes(subscriptionValue);
                const isVisible = matchesSearch && matchesStatus && matchesSubscription;
                row.dataset.filteredOut = isVisible ? 'false' : 'true';
                row.hidden = !isVisible;
            });

            refreshPaginations();
        }

        if (searchInput) searchInput.addEventListener('input', filterMembers);
        if (filterStatus) filterStatus.addEventListener('change', filterMembers);
        if (filterSubscription) filterSubscription.addEventListener('change', filterMembers);
        filterMembers();
    }

    // ---------- جستجوی عضو در تنظیمات پیامک ----------
    const memberSearchInput = document.getElementById('memberSearchInput');
    if (memberSearchInput) {
        memberSearchInput.addEventListener('input', function () {
            const searchValue = this.value.trim().toLowerCase();
            const memberRows = document.querySelectorAll('.member-selection-table tbody tr');

            memberRows.forEach(function (row) {
                row.hidden = !row.cells[0].textContent.toLowerCase().includes(searchValue);
            });
        });
    }

    // ---------- فرم اعلانیه (لیست پیامک‌ها) ----------
    const announcementForm = document.getElementById('announcementForm');
    if (announcementForm) {
        announcementForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const classSelect = document.getElementById('announcementClassSelect');
            const selectedCount = classSelect ? classSelect.selectedOptions.length : 0;
            showToast('اعلانیه برای ' + faDigits(selectedCount) + ' کلاس انتخاب‌شده ثبت و در صف ارسال قرار گرفت.');
        });
    }

    const announcementTypeOptions = document.querySelectorAll('.announcement-type-option');
    const announcementMessage = document.getElementById('announcementMessage');
    if (announcementTypeOptions.length && announcementMessage) {
        announcementTypeOptions.forEach(function (option) {
            option.addEventListener('change', function () {
                announcementMessage.value = this.dataset.message;
            });
        });
    }

    const announcementClassSearch = document.getElementById('announcementClassSearch');
    const announcementClassSelect = document.getElementById('announcementClassSelect');
    if (announcementClassSearch && announcementClassSelect) {
        announcementClassSearch.addEventListener('input', function () {
            const searchValue = this.value.trim().toLowerCase();

            Array.from(announcementClassSelect.options).forEach(function (option) {
                option.hidden = searchValue ? !option.textContent.toLowerCase().includes(searchValue) : false;
            });
        });

        const announcementSelectAll = document.getElementById('announcementSelectAll');
        if (announcementSelectAll) {
            announcementSelectAll.addEventListener('change', function () {
                Array.from(announcementClassSelect.options).forEach(function (option) {
                    option.selected = announcementSelectAll.checked;
                });
            });
        }
    }

    // ---------- تنظیمات پیامک ----------
    const smsSettingsForm = document.getElementById('smsSettingsForm');
    if (smsSettingsForm) {
        smsSettingsForm.addEventListener('submit', function (event) {
            event.preventDefault();
            showToast('تنظیمات پیامک ذخیره شد.');
        });
    }

    const memberSmsSaveBtn = document.getElementById('memberSmsSaveBtn');
    if (memberSmsSaveBtn) {
        memberSmsSaveBtn.addEventListener('click', function () {
            showToast('تنظیمات پیامک اعضا ذخیره شد.');
        });
    }

    // ---------- فیلتر روز در لیست کلاس‌ها ----------
    const classDayFilter = document.getElementById('classDayFilter');
    const classTable = document.getElementById('classTable');
    if (classDayFilter && classTable) {
        const classRows = classTable.querySelectorAll('tbody tr');
        const classResultCount = document.getElementById('classResultCount');
        const classEmptyState = document.getElementById('classEmptyState');

        classDayFilter.addEventListener('change', function () {
            let visibleClassCount = 0;
            classRows.forEach(function (row) {
                const matchesFilter = !this.value || row.dataset.days.split(' ').includes(this.value);
                row.dataset.filteredOut = matchesFilter ? 'false' : 'true';
                row.hidden = !matchesFilter;
                if (matchesFilter) {
                    visibleClassCount += 1;
                }
            }, this);

            if (classResultCount) {
                classResultCount.textContent = faDigits(visibleClassCount) + ' کلاس';
            }
            if (classEmptyState) {
                classEmptyState.hidden = visibleClassCount > 0;
            }
            refreshPaginations();
        });
    }

    // ---------- ویرایش پلن‌ها و قیمت‌های کلاس ----------
    const classPlansModal = document.getElementById('classPlansModal');
    const classPlansRows = document.getElementById('classPlansRows');
    const classPlansForm = document.getElementById('classPlansForm');
    const addClassPlan = document.getElementById('addClassPlan');
    let editingClassPlanCell = null;
    if (classPlansModal && classPlansRows && classPlansForm) {
        function addClassPlanRow(name, price) {
            const row = document.createElement('div');
            row.className = 'class-plan-editor-row';
            row.innerHTML = `<select class="form-select class-plan-name"><option ${name === '۱۲ جلسه' ? 'selected' : ''}>۱۲ جلسه</option><option ${name === '۳۶ جلسه' ? 'selected' : ''}>۳۶ جلسه</option><option ${name === '۱۲۰ جلسه' ? 'selected' : ''}>۱۲۰ جلسه</option></select><input class="form-control class-plan-price" type="number" min="0" value="${normalizeDigits(price).replace(/[^0-9]/g, '')}" placeholder="قیمت تومان"><button type="button" class="btn btn-outline-danger remove-class-plan" title="حذف"><i class="fas fa-trash"></i></button>`;
            classPlansRows.appendChild(row);
        }

        document.querySelectorAll('.edit-class-plans').forEach(function (button) {
            button.addEventListener('click', function () {
                editingClassPlanCell = button.closest('tr').querySelector('.class-plans-cell');
                classPlansRows.innerHTML = '';
                editingClassPlanCell.querySelectorAll('.badge').forEach(function (badge) {
                    const parts = badge.textContent.split(':');
                    addClassPlanRow(parts[0].trim(), parts[1] || '');
                });
                document.getElementById('classPlansDescription').textContent = `قیمت‌های کلاس ${button.dataset.class} را ویرایش کنید.`;
                bootstrap.Modal.getOrCreateInstance(classPlansModal).show();
            });
        });

        addClassPlan.addEventListener('click', function () {
            addClassPlanRow('۱۲ جلسه', '');
        });

        classPlansRows.addEventListener('click', function (event) {
            const removeButton = event.target.closest('.remove-class-plan');
            if (removeButton) removeButton.closest('.class-plan-editor-row').remove();
        });

        classPlansForm.addEventListener('submit', function (event) {
            event.preventDefault();
            if (!editingClassPlanCell) return;
            const actionButton = editingClassPlanCell.querySelector('.edit-class-plans');
            editingClassPlanCell.innerHTML = '';
            classPlansRows.querySelectorAll('.class-plan-editor-row').forEach(function (row) {
                const name = row.querySelector('.class-plan-name').value;
                const price = row.querySelector('.class-plan-price').value;
                if (!price) return;
                const badge = document.createElement('span');
                badge.className = 'badge bg-light text-dark';
                badge.textContent = `${name}: ${formatCurrency(price)}`;
                editingClassPlanCell.appendChild(badge);
            });
            if (actionButton) editingClassPlanCell.appendChild(actionButton);
            bootstrap.Modal.getOrCreateInstance(classPlansModal).hide();
        });
    }

    // ---------- تمدید اشتراک باشگاه (پروفایل) ----------
    const renewSubscriptionForm = document.getElementById('renewSubscriptionForm');
    const subscriptionPlan = document.getElementById('subscriptionPlan');
    const subscriptionPrice = document.getElementById('gymSubscriptionPrice');
    const subscriptionStatus = document.getElementById('gymSubscriptionStatus');
    if (renewSubscriptionForm && subscriptionPlan) {
        subscriptionPlan.addEventListener('change', function () {
            const selectedPlan = this.options[this.selectedIndex];
            subscriptionPrice.textContent = selectedPlan.dataset.price;
        });

        renewSubscriptionForm.addEventListener('submit', function (event) {
            event.preventDefault();
            subscriptionStatus.className = 'badge bg-warning';
            subscriptionStatus.textContent = 'در انتظار پرداخت';
            bootstrap.Modal.getOrCreateInstance(document.getElementById('renewSubscriptionModal')).hide();
            showToast('درخواست تمدید اشتراک با موفقیت ثبت شد.');
        });
    }

    // ---------- مدیریت کاربران پذیرش (پروفایل) ----------
    const receptionistForm = document.getElementById('receptionistForm');
    const receptionistTableBody = document.getElementById('receptionistTableBody');
    const showReceptionistForm = document.getElementById('showReceptionistForm');
    const cancelReceptionistForm = document.getElementById('cancelReceptionistForm');
    const receptionistPassword = document.getElementById('receptionistPassword');
    let editingReceptionistRow = null;
    if (receptionistForm && receptionistTableBody) {
        const receptionistModal = document.getElementById('receptionistModal');

        if (showReceptionistForm) {
            showReceptionistForm.addEventListener('click', function () {
                receptionistForm.reset();
                receptionistPassword.required = true;
                editingReceptionistRow = null;
                if (receptionistModal) {
                    receptionistModal.querySelector('.modal-title').textContent = 'ایجاد کاربر پذیرش';
                }
            });
        }

        if (cancelReceptionistForm) {
            cancelReceptionistForm.addEventListener('click', function () {
                receptionistForm.reset();
                receptionistPassword.required = true;
                editingReceptionistRow = null;
            });
        }

        receptionistForm.addEventListener('submit', function (event) {
            event.preventDefault();

            const username = document.getElementById('receptionistUsername').value.trim();
            const phone = document.getElementById('receptionistPhone').value.trim();
            if (!username || !phone) {
                return;
            }

            if (editingReceptionistRow) {
                editingReceptionistRow.cells[0].textContent = username;
                editingReceptionistRow.cells[1].textContent = phone;
                receptionistForm.reset();
                receptionistPassword.required = true;
                editingReceptionistRow = null;
                if (receptionistModal) {
                    bootstrap.Modal.getOrCreateInstance(receptionistModal).hide();
                }
                showToast('اطلاعات کاربر پذیرش به‌روزرسانی شد.');
                return;
            }

            const row = document.createElement('tr');
            const usernameCell = document.createElement('td');
            const phoneCell = document.createElement('td');
            const roleCell = document.createElement('td');
            const statusCell = document.createElement('td');
            const actionsCell = document.createElement('td');
            const roleBadge = document.createElement('span');
            const statusBadge = document.createElement('span');
            const editButton = document.createElement('button');
            const toggleButton = document.createElement('button');
            const deleteButton = document.createElement('button');

            usernameCell.textContent = username;
            phoneCell.textContent = phone;
            roleBadge.className = 'badge bg-secondary';
            roleBadge.textContent = 'پذیرش';
            statusBadge.className = 'badge bg-success status-badge';
            statusBadge.textContent = 'فعال';
            editButton.type = 'button';
            editButton.className = 'btn btn-sm btn-info edit-receptionist';
            editButton.innerHTML = '<i class="fas fa-edit"></i> ویرایش';
            toggleButton.type = 'button';
            toggleButton.className = 'btn btn-sm btn-warning toggle-receptionist receptionist-status-toggle';
            toggleButton.innerHTML = '<i class="fas fa-user-slash"></i> غیرفعال کردن';
            deleteButton.type = 'button';
            deleteButton.className = 'btn btn-sm btn-danger delete-receptionist';
            deleteButton.innerHTML = '<i class="fas fa-trash"></i> حذف';

            roleCell.appendChild(roleBadge);
            statusCell.appendChild(statusBadge);
            actionsCell.append(editButton, toggleButton, deleteButton);
            row.append(usernameCell, phoneCell, roleCell, statusCell, actionsCell);
            receptionistTableBody.appendChild(row);
            receptionistForm.reset();
            receptionistPassword.required = true;
            if (receptionistModal) {
                bootstrap.Modal.getOrCreateInstance(receptionistModal).hide();
            }
            showToast('کاربر پذیرش جدید ایجاد شد.');
        });

        receptionistTableBody.addEventListener('click', function (event) {
            const editButton = event.target.closest('.edit-receptionist');
            const toggleButton = event.target.closest('.toggle-receptionist');
            const deleteButton = event.target.closest('.delete-receptionist');

            if (editButton) {
                editingReceptionistRow = editButton.closest('tr');
                document.getElementById('receptionistUsername').value = editingReceptionistRow.cells[0].textContent.trim();
                document.getElementById('receptionistPhone').value = editingReceptionistRow.cells[1].textContent.trim();
                receptionistPassword.value = '';
                receptionistPassword.required = false;
                if (receptionistModal) {
                    receptionistModal.querySelector('.modal-title').textContent = 'ویرایش کاربر پذیرش';
                    bootstrap.Modal.getOrCreateInstance(receptionistModal).show();
                }
                document.getElementById('receptionistUsername').focus();
                return;
            }

            if (toggleButton) {
                const statusBadge = toggleButton.closest('tr').querySelector('.status-badge');
                const isActive = statusBadge.classList.contains('bg-success');
                statusBadge.classList.toggle('bg-success', !isActive);
                statusBadge.classList.toggle('bg-secondary', isActive);
                statusBadge.textContent = isActive ? 'غیرفعال' : 'فعال';
                toggleButton.innerHTML = isActive
                    ? '<i class="fas fa-user-check"></i> فعال کردن'
                    : '<i class="fas fa-user-slash"></i> غیرفعال کردن';
            }

            if (deleteButton) {
                const confirmed = window.confirm('آیا از حذف این کاربر پذیرش مطمئن هستید؟');
                if (confirmed) {
                    deleteButton.closest('tr').remove();
                }
            }
        });
    }

    // ---------- ویرایش اطلاعات پروفایل ----------
    const editProfileForm = document.getElementById('editProfileForm');
    if (editProfileForm) {
        editProfileForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const setField = function (id, value) {
                const element = document.getElementById(id);
                if (element) element.textContent = value;
            };
            const firstName = document.getElementById('editFirstName').value.trim();
            const lastName = document.getElementById('editLastName').value.trim();
            setField('profileFirstName', firstName);
            setField('profileLastName', lastName);
            setField('profileEmail', document.getElementById('editEmail').value.trim());
            setField('profilePhone', document.getElementById('editPhone').value.trim());
            setField('profileFullName', [firstName, lastName].filter(Boolean).join(' ') || 'مدیر سیستم');
            bootstrap.Modal.getOrCreateInstance(document.getElementById('editProfileModal')).hide();
            showToast('اطلاعات پروفایل به‌روزرسانی شد.');
        });
    }

    // ---------- تغییر رمز عبور ----------
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const newPassword = document.getElementById('newPassword').value;
            const newPasswordRepeat = document.getElementById('newPasswordRepeat').value;
            if (newPassword && newPassword === newPasswordRepeat) {
                bootstrap.Modal.getOrCreateInstance(document.getElementById('changePasswordModal')).hide();
                changePasswordForm.reset();
                showToast('رمز عبور با موفقیت تغییر کرد.');
            } else {
                showToast('تکرار رمز عبور با رمز جدید یکسان نیست.', 'danger');
            }
        });
    }

    // ---------- ثبت حضور و غیاب ----------
    const attendanceTable = document.getElementById('attendanceTable');
    if (attendanceTable) {
        const attendanceDate = document.getElementById('attendanceDate');
        if (attendanceDate) {
            attendanceDate.value = todayJalali();
        }

        const initialAttendanceState = [];
        attendanceTable.querySelectorAll('tbody tr').forEach(function (row) {
            const checked = row.querySelector('.btn-check:checked');
            initialAttendanceState.push(checked ? checked.id : null);
        });

        function selectedStatusLabel(row) {
            const checked = row.querySelector('.btn-check:checked');
            if (!checked) return '';
            const label = row.querySelector('label[for="' + checked.id + '"]');
            return label ? label.textContent.trim() : '';
        }

        function paintAttendanceRow(row) {
            row.classList.remove('table-success', 'table-danger', 'table-warning');
            const checked = row.querySelector('.btn-check:checked');
            if (!checked) return;
            if (checked.id.includes('present')) {
                row.classList.add('table-success');
            } else if (checked.id.includes('absent') && checked.id.includes('excused') === false) {
                row.classList.add('table-danger');
            } else if (checked.id.includes('excused')) {
                row.classList.add('table-warning');
            }
        }

        document.querySelectorAll('.btn-check').forEach(function (radio) {
            radio.addEventListener('change', function () {
                const row = this.closest('tr');
                if (row) {
                    paintAttendanceRow(row);
                }
            });
        });

        const loadAttendanceBtn = document.getElementById('loadAttendanceBtn');
        if (loadAttendanceBtn) {
            loadAttendanceBtn.addEventListener('click', function () {
                showToast('لیست حضور اعضای کلاس انتخابی بارگذاری شد.', 'info');
            });
        }

        document.querySelectorAll('.submit-attendance').forEach(function (button) {
            button.addEventListener('click', function () {
                const row = this.closest('tr');
                showToast('وضعیت «' + selectedStatusLabel(row) + '» برای ' + row.cells[1].textContent.trim() + ' ثبت شد.');
            });
        });

        const submitAllAttendanceBtn = document.getElementById('submitAllAttendanceBtn');
        if (submitAllAttendanceBtn) {
            submitAllAttendanceBtn.addEventListener('click', function () {
                const count = attendanceTable.querySelectorAll('tbody tr').length;
                showToast('حضور و غیاب ' + faDigits(count) + ' عضو با موفقیت ثبت شد.');
            });
        }

        const resetAttendanceBtn = document.getElementById('resetAttendanceBtn');
        if (resetAttendanceBtn) {
            resetAttendanceBtn.addEventListener('click', function () {
                attendanceTable.querySelectorAll('tbody tr').forEach(function (row, index) {
                    row.querySelectorAll('.btn-check').forEach(function (radio) {
                        radio.checked = radio.id === initialAttendanceState[index];
                    });
                    paintAttendanceRow(row);
                });
                showToast('وضعیت حضور و غیاب به حالت اولیه بازگشت.', 'info');
            });
        }
    }

    // ---------- فیلتر تاریخچه حضور و غیاب ----------
    const historyFilterBtn = document.getElementById('historyFilterBtn');
    const historyTable = document.getElementById('historyTable');
    if (historyFilterBtn && historyTable) {
        historyFilterBtn.addEventListener('click', function () {
            const searchInput = document.getElementById('historySearch');
            const fromDate = document.getElementById('historyFromDate');
            const toDate = document.getElementById('historyToDate');
            const searchValue = searchInput ? searchInput.value.trim().toLowerCase() : '';
            const from = fromDate ? normalizeDigits(fromDate.value.trim()).replace(/[^0-9/]/g, '') : '';
            const to = toDate ? normalizeDigits(toDate.value.trim()).replace(/[^0-9/]/g, '') : '';
            let visibleCount = 0;

            historyTable.querySelectorAll('tbody tr').forEach(function (row) {
                const member = row.cells[2].textContent.toLowerCase();
                const date = normalizeDigits(row.cells[0].textContent.trim()).replace(/[^0-9/]/g, '');
                const matchesSearch = !searchValue || member.includes(searchValue);
                const matchesFrom = !from || date >= from;
                const matchesTo = !to || date <= to;
                const isVisible = matchesSearch && matchesFrom && matchesTo;
                row.dataset.filteredOut = isVisible ? 'false' : 'true';
                row.hidden = !isVisible;
                if (isVisible) visibleCount += 1;
            });

            showToast(faDigits(visibleCount) + ' رکورد نمایش داده شد.', 'info');
            refreshPaginations();
        });
    }

    // ---------- تغییر وضعیت حضور در جزئیات کلاس ----------
    const statusCycle = { 'حاضر': 'غایب', 'غایب': 'غیبت موجه', 'غیبت موجه': 'حاضر' };
    const statusCycleClass = { 'حاضر': 'bg-success', 'غایب': 'bg-danger', 'غیبت موجه': 'bg-warning' };
    document.querySelectorAll('.toggle-attendance-status').forEach(function (button) {
        button.addEventListener('click', function () {
            const badge = this.closest('tr').querySelector('.badge');
            const next = statusCycle[badge.textContent.trim()] || 'حاضر';
            badge.textContent = next;
            badge.className = 'badge ' + statusCycleClass[next];
        });
    });

    // ---------- بازه گزارش در امور مالی ----------
    const financePeriod = document.getElementById('financePeriod');
    if (financePeriod) {
        const financeBars = document.querySelector('.finance-bars-large');
        const financeRangeBadge = document.getElementById('financeRangeBadge');
        const periodLabels = { 'ماه جاری': 'ماه جاری', 'سه ماه اخیر': '۳ ماه اخیر', 'سال جاری': '۶ ماه اخیر' };
        const periodVisibleMonths = { 'ماه جاری': 1, 'سه ماه اخیر': 3, 'سال جاری': 6 };

        financePeriod.addEventListener('change', function () {
            if (!financeBars) return;
            const months = financeBars.querySelectorAll('.finance-month');
            const visibleCount = periodVisibleMonths[this.value] || 6;
            months.forEach(function (month, index) {
                month.hidden = index < months.length - visibleCount;
            });
            if (financeRangeBadge) {
                financeRangeBadge.textContent = periodLabels[this.value] || '۶ ماه اخیر';
            }
        });
    }

    // ---------- دکمه‌های بازه زمانی داشبورد ----------
    const dashboardRangeButtons = document.querySelectorAll('.dashboard-range-btn');
    dashboardRangeButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            dashboardRangeButtons.forEach(function (item) {
                item.classList.remove('active');
            });
            this.classList.add('active');
        });
    });

    // ---------- فرم ورود ----------
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function (event) {
            event.preventDefault();
            window.location.href = 'dashboard.html';
        });
    }

    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', function (event) {
            event.preventDefault();
            showToast('برای بازیابی رمز عبور با پشتیبانی تماس بگیرید.', 'info');
        });
    }

    // ---------- فرم درخواست تماس (صفحه اصلی) ----------
    const contactForm = document.getElementById('contact');
    if (contactForm) {
        contactForm.addEventListener('submit', function (event) {
            event.preventDefault();
            contactForm.reset();
            showToast('درخواست تماس شما ثبت شد؛ به‌زودی با شما تماس می‌گیریم.');
        });
    }

    // ---------- تنظیمات باشگاه و پیش‌نمایش زنده ----------
    const gymSettingsForm = document.getElementById('gymSettingsForm');
    if (gymSettingsForm) {
        const gymName = document.getElementById('gymName');
        const gymPhone = document.getElementById('gymPhone');
        const gymAddress = document.getElementById('gymAddress');
        const gymColor = document.getElementById('gymColor');
        const previewBox = document.querySelector('.preview-box');

        function syncSettingsPreview() {
            if (!previewBox) return;
            const previewName = document.getElementById('previewName');
            const previewPhone = document.getElementById('previewPhone');
            const previewAddress = document.getElementById('previewAddress');
            if (previewName && gymName) previewName.textContent = gymName.value;
            if (previewPhone && gymPhone) previewPhone.textContent = gymPhone.value;
            if (previewAddress && gymAddress) previewAddress.textContent = gymAddress.value;
            if (gymColor) previewBox.style.backgroundColor = gymColor.value;
        }

        [gymName, gymPhone, gymAddress, gymColor].forEach(function (input) {
            if (input) input.addEventListener('input', syncSettingsPreview);
        });

        gymSettingsForm.addEventListener('submit', function (event) {
            event.preventDefault();
            showToast('تنظیمات باشگاه ذخیره شد.');
        });
    }

    // ---------- ثبت پرداخت دستی ----------
    const paymentForm = document.getElementById('manualPaymentForm');
    const paymentTable = document.getElementById('paymentTable');
    const paymentSearch = document.getElementById('paymentSearch');
    const paymentStatusFilter = document.getElementById('paymentStatusFilter');
    const paymentResultCount = document.getElementById('paymentResultCount');
    if (paymentForm && paymentTable) {
        const paymentDate = document.getElementById('paymentDate');
        if (paymentDate) {
            paymentDate.value = todayJalali();
        }

        paymentForm.addEventListener('submit', function (event) {
            event.preventDefault();

            const member = document.getElementById('paymentMember').value;
            const amount = document.getElementById('paymentAmount').value;
            const plan = document.getElementById('paymentPlan').value;
            const date = document.getElementById('paymentDate').value.trim();
            const status = document.getElementById('paymentStatus').value;
            const reference = document.getElementById('paymentReference').value.trim() || `TRX${Date.now().toString().slice(-6)}`;
            if (!member || !amount || !date) {
                return;
            }

            const row = document.createElement('tr');
            row.innerHTML = `<td>${escapeHtml(member)}</td><td>${formatCurrency(amount)}</td><td>${escapeHtml(plan)}</td><td>${escapeHtml(date)}</td><td><span class="badge ${statusBadgeClass(status)}">${escapeHtml(status)}</span></td><td>${escapeHtml(reference)}</td><td><button type="button" class="btn btn-sm btn-outline-danger delete-payment" title="حذف"><i class="fas fa-trash"></i></button></td>`;
            paymentTable.querySelector('tbody').prepend(row);
            addDeleteHandler(row.querySelector('.delete-payment'), row);
            paymentForm.reset();
            paymentDate.value = todayJalali();
            bootstrap.Modal.getOrCreateInstance(document.getElementById('paymentModal')).hide();
            filterPayments();
            showToast('پرداخت با موفقیت ثبت شد.');
        });

        paymentTable.querySelectorAll('.delete-payment').forEach(function (button) {
            addDeleteHandler(button, button.closest('tr'));
        });

        function filterPayments() {
            const searchValue = (paymentSearch ? paymentSearch.value : '').trim().toLowerCase();
            const statusValue = paymentStatusFilter ? paymentStatusFilter.value : '';
            let visibleCount = 0;
            paymentTable.querySelectorAll('tbody tr').forEach(function (row) {
                const matchesSearch = !searchValue || row.cells[0].textContent.toLowerCase().includes(searchValue) || row.cells[5].textContent.toLowerCase().includes(searchValue);
                const matchesStatus = !statusValue || row.cells[4].textContent.trim() === statusValue;
                row.dataset.filteredOut = matchesSearch && matchesStatus ? 'false' : 'true';
                row.hidden = !(matchesSearch && matchesStatus);
                if (!row.hidden) {
                    visibleCount += 1;
                }
            });
            if (paymentResultCount) {
                paymentResultCount.textContent = faDigits(visibleCount) + ' تراکنش نمایش داده شد';
            }
            refreshPaginations();
        }

        if (paymentSearch) paymentSearch.addEventListener('input', filterPayments);
        if (paymentStatusFilter) paymentStatusFilter.addEventListener('change', filterPayments);
        filterPayments();
    }

    // ---------- ثبت هزینه ----------
    const expenseForm = document.getElementById('expenseForm');
    const expenseTable = document.getElementById('expenseTable');
    const expenseSearch = document.getElementById('expenseSearch');
    const expenseCategoryFilter = document.getElementById('expenseCategoryFilter');
    const expenseResultCount = document.getElementById('expenseResultCount');
    if (expenseForm && expenseTable) {
        const expenseDate = document.getElementById('expenseDate');
        if (expenseDate) {
            expenseDate.value = todayJalali();
        }

        expenseForm.addEventListener('submit', function (event) {
            event.preventDefault();

            const title = document.getElementById('expenseTitle').value.trim();
            const amount = document.getElementById('expenseAmount').value;
            const category = document.getElementById('expenseCategory').value;
            const vendor = document.getElementById('expenseVendor').value.trim() || 'ثبت دستی';
            const date = document.getElementById('expenseDate').value.trim();
            const status = document.getElementById('expenseStatus').value;
            if (!title || !amount || !category || !date) {
                return;
            }

            const row = document.createElement('tr');
            row.innerHTML = `<td>${escapeHtml(title)}</td><td>${escapeHtml(category)}</td><td>${escapeHtml(vendor)}</td><td>${formatCurrency(amount)}</td><td>${escapeHtml(date)}</td><td><span class="badge ${statusBadgeClass(status)}">${escapeHtml(status)}</span></td><td><button type="button" class="btn btn-sm btn-outline-danger delete-expense" title="حذف"><i class="fas fa-trash"></i></button></td>`;
            expenseTable.querySelector('tbody').prepend(row);
            addDeleteHandler(row.querySelector('.delete-expense'), row);
            expenseForm.reset();
            expenseDate.value = todayJalali();
            bootstrap.Modal.getOrCreateInstance(document.getElementById('expenseModal')).hide();
            filterExpenses();
            showToast('هزینه جدید ثبت شد.');
        });

        expenseTable.querySelectorAll('.delete-expense').forEach(function (button) {
            addDeleteHandler(button, button.closest('tr'));
        });

        function filterExpenses() {
            const searchValue = (expenseSearch ? expenseSearch.value : '').trim().toLowerCase();
            const categoryValue = expenseCategoryFilter ? expenseCategoryFilter.value : '';
            let visibleCount = 0;
            expenseTable.querySelectorAll('tbody tr').forEach(function (row) {
                const matchesSearch = !searchValue || row.cells[0].textContent.toLowerCase().includes(searchValue) || row.cells[2].textContent.toLowerCase().includes(searchValue);
                const matchesCategory = !categoryValue || row.cells[1].textContent.trim() === categoryValue;
                row.dataset.filteredOut = matchesSearch && matchesCategory ? 'false' : 'true';
                row.hidden = !(matchesSearch && matchesCategory);
                if (!row.hidden) {
                    visibleCount += 1;
                }
            });
            if (expenseResultCount) {
                expenseResultCount.textContent = faDigits(visibleCount) + ' هزینه نمایش داده شد';
            }
            refreshPaginations();
        }

        if (expenseSearch) expenseSearch.addEventListener('input', filterExpenses);
        if (expenseCategoryFilter) expenseCategoryFilter.addEventListener('change', filterExpenses);
        filterExpenses();
    }

    // ---------- پاک‌سازی backdrop مودال‌ها ----------
    document.querySelectorAll('.modal').forEach(function (modal) {
        modal.addEventListener('hidden.bs.modal', function () {
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        });
    });
});
