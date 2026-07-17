from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render


def _is_admin_sys(user):
    return user.is_authenticated and user.role == 'ADMIN_SYS'


@login_required
@user_passes_test(_is_admin_sys)
def monitoring_dashboard(request):
    return render(request, 'monitoring/dashboard.html')
