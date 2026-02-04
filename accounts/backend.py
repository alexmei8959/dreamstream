from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from . import app_settings
from .forms import EmailValidationForm, UsernameValidationForm
from .models import userstatus
from datetime import datetime

User = get_user_model()


class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        """Authenticate with email/username and password"""

        login = kwargs.get("login", kwargs.get("username", None))
        password = kwargs.get("password", None)

        if login and password:

            lookup_obj = Q()

            authentication_methods = app_settings.AUTHENTICATION_METHODS
            if (
                app_settings.AuthenticationMethod.EMAIL in authentication_methods
                and EmailValidationForm({"email": login}).is_valid()
            ):
                lookup_obj |= Q(email__iexact=login)
            elif (
                app_settings.AuthenticationMethod.USERNAME in authentication_methods
                and UsernameValidationForm({"username": login}).is_valid()
            ):
                lookup_obj |= Q(username__exact=login)
            else:
                return None

            if lookup_obj:
                try:
                    user = User.objects.get(lookup_obj)
                    qsUserStatus = userstatus.objects.get(user=user)
                    # 判斷帳號是否已鎖定
                    if qsUserStatus.is_lock:
                        current_time = timezone.now()
                        diff = current_time - qsUserStatus.lock_date
                        minutes_diff = diff.total_seconds() / 60
                        # 鎖定多久時間
                        if minutes_diff < app_settings.ACCOUNT_LOCK_MIN:
                            messages.add_message(request, messages.ERROR, '此帳號已鎖定')
                            return None
                        else:
                            # 時間到要解鎖
                            userstatus.objects.filter(user=user).update(is_lock=False, loginfail_times=0)
                            qsUserStatus = userstatus.objects.get(user=user)

                    # 驗證帳號
                    if not user.check_password(password):
                        # 記錄錯誤
                        userstatus.objects.filter(user=user).update(loginfail_times=qsUserStatus.loginfail_times + 1)
                        if qsUserStatus.loginfail_times + 1 >= app_settings.ACCOUNT_LOCK_TIMES:
                            userstatus.objects.filter(user=user).update(is_lock=True, lock_date=datetime.now())
                            messages.add_message(request, messages.ERROR, '此帳號已鎖定')
                            return None
                        messages.add_message(request, messages.ERROR, '帳號或密碼錯誤')
                        return None
                    if not self.user_can_authenticate(user):
                        messages.add_message(request, messages.ERROR, '帳號已停用')
                        return None

                    # 錯誤歸零
                    userstatus.objects.filter(user=user).update(loginfail_times=0)

                    return user
                except User.DoesNotExist:
                    messages.add_message(request, messages.ERROR, '帳號或密碼錯誤')
                    return None

        return None
