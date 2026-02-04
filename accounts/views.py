import shortuuid
import logging
import json
import time
import os
import hmac
import hashlib

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Permission, User
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    get_user,
    update_session_auth_hash,
)
from django.contrib.messages import get_messages
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.conf import settings
from google.api_core.exceptions import GoogleAPICallError
from  google.cloud import recaptchaenterprise_v1

from commons.models import menugroup, parameter
from commons.tools import SendEmail
from .models import userstatus, userprofile, PasswordResetToken
from .forms import LoginForm
from . import app_settings

logger = logging.getLogger("django")


class CustomLoginView(LoginView):
    """登入"""

    form_class = LoginForm
    template_name = "accounts/login.html"

    def form_valid(self, form):
        """登入驗證"""
        try:
            # --- reCAPTCHA Verification ---
            expected_recaptcha_action = (
                "login"  # MUST match the action in your frontend JavaScript
            )
            assessment = self.create_assessment(expected_recaptcha_action)

            if not self.is_recaptcha_valid(assessment, expected_recaptcha_action):
                # reCAPTCHA failed - add error and redisplay form
                logger.warning(
                    f"reCAPTCHA verification failed for user attempt: {form.cleaned_data.get('login')}"
                )
                form.add_error(
                    None, "無效的 reCAPTCHA 驗證，請重試。"
                )  # Add non-field error
                # Optionally add a message: messages.error(self.request, "Invalid reCAPTCHA. Please try again.")
                return self.form_invalid(form)

            # --- reCAPTCHA Passed - Proceed with Login ---
            logger.info(
                f"reCAPTCHA verification succeeded for user attempt: {form.cleaned_data.get('login')}"
            )

            user = form.cleaned_data["user"]

            # session 暫存（如果otp可使用到）
            self.request.session["user_name"] = user.get_username()
            self.request.session["user_email"] = user.email
            self.request.session["is_superuser"] = user.is_superuser

            profile = userprofile.objects.filter(user=user).first()

            # === 使用 Email OTP ===
            if profile and profile.is_otp:
                otp_code = generate_email_otp(user.email)

                # OTP 專用 session
                self.request.session["otp_user_id"] = user.id
                self.request.session["otp_attempts"] = 0
                self.request.session["otp_created_at"] = int(time.time())

                # 寄送 Email OTP
                context = {
                    "user": user.first_name,
                    "user_email": user.email,
                    "otp_code": otp_code,
                    "expire_minutes": 5,
                }
                SendEmail("otp_login").send(**context)

                return HttpResponseRedirect(reverse_lazy("accounts:otp_login"))

            # === 一般登入（未啟用 OTP） ===
            login(self.request, user)
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            logger.error(e)
            return HttpResponseRedirect(reverse_lazy("accounts:login"))

    def create_assessment(
        self, recaptcha_action: str
    ) -> recaptchaenterprise_v1.Assessment | None:
        """Creates an assessment to verify the reCAPTCHA token."""
        recaptcha_response_token = self.request.POST.get("g-recaptcha-response")
        if not recaptcha_response_token:
            logger.warning("reCAPTCHA token not found in POST data.")
            return None

        try:
            if settings.DEBUG:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                    "smart-spark-382102-3218296800ed.json"
                )

            client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()
            project_id = settings.GOOGLE_RECAPTCHA_ENTERPRISE_PROJECT_ID
            site_key = settings.GOOGLE_RECAPTCHA_ENTERPRISE_SITE_KEY

            # Build the assessment request.
            assessment = recaptchaenterprise_v1.Assessment()
            assessment.event.token = recaptcha_response_token
            assessment.event.site_key = site_key
            # assessment.event.expected_action = recaptcha_action # Add this if you want strict action matching

            project_name = f"projects/{project_id}"

            request = recaptchaenterprise_v1.CreateAssessmentRequest(
                parent=project_name,
                assessment=assessment,
            )

            response = client.create_assessment(request=request)
            logger.info(
                f"reCAPTCHA assessment response received. Name: {response.name}"
            )
            return response

        except GoogleAPICallError as e:
            logger.error(f"Could not create reCAPTCHA assessment: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during reCAPTCHA assessment: {e}",
                exc_info=True,
            )
            return None

    def is_recaptcha_valid(
        self, assessment: recaptchaenterprise_v1.Assessment, expected_action: str
    ) -> bool:
        """Checks if the assessment is valid based on score and action."""
        if not assessment:
            return False

        # Check if the token is valid.
        if not assessment.token_properties.valid:
            logger.warning(
                f"reCAPTCHA token invalid: {assessment.token_properties.invalid_reason.name}"
            )
            return False

        # Check if the expected action matches. IMPORTANT: Match the action string from your JS ('login').
        # If you didn't set assessment.event.expected_action above, this check might be less strict
        # depending on your Google Cloud console settings. It's better to check explicitly.
        if assessment.token_properties.action != expected_action:
            logger.warning(
                f"reCAPTCHA action mismatch: Expected '{expected_action}', "
                f"Got '{assessment.token_properties.action}'"
            )
            # Decide if this is a hard failure or just a warning based on your policy
            return False  # Treat action mismatch as failure for security

        # Check the score (0.0 = high risk, 1.0 = low risk).
        score = assessment.risk_analysis.score
        required_score = getattr(
            settings, "RECAPTCHA_REQUIRED_SCORE", 0.5
        )  # Default to 0.5 if not set
        logger.info(f"reCAPTCHA score: {score} (Threshold: {required_score})")
        if score < required_score:
            logger.warning(f"reCAPTCHA score {score} below threshold {required_score}.")
            return False

        # All checks passed
        return True


class NormalLogoutView(View):
    """登出"""

    def get(self, request, *args, **kwargs):
        success_url = app_settings.LOGOUT_REDIRECT_URL
        #  將session中使用者資訊清空
        self.request.session.flush()
        logout(request)
        return HttpResponseRedirect(success_url)


class ChangePasswordView(View):
    """變更密碼"""

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        re_new_password = data.get("re_new_password")

        is_clean, error = self._clean(
            request, old_password, new_password, re_new_password
        )
        if is_clean:
            user = get_user(request)
            user.set_password(new_password)
            update_session_auth_hash(request, user)
            user.save()
            # 變更密碼時要記錄前三次密碼
            if user:
                qsUserStatus = userstatus.objects.filter(user=user).first()
                qsUserStatus.password3 = qsUserStatus.password2
                qsUserStatus.password2 = qsUserStatus.password1
                qsUserStatus.password1 = user.password
                qsUserStatus.save()

            return JsonResponse({"message": "success"})
        else:
            return JsonResponse({"message": error})

    def _clean(self, request, old_password, new_password, re_new_password):
        error = ""
        user = get_user(request)

        if user.check_password(old_password) is False:
            error = "舊密碼輸入錯誤"
            return False, error

        if old_password == new_password:
            error = "新的密碼不能跟舊的密碼一樣"
            return False, error

        if new_password != re_new_password:
            error = "二次新密碼不一致"
            return False, error

        # 驗證新密碼與資料庫歷史紀錄前三次是否相同
        qsUserStatus = userstatus.objects.filter(user=user).first()
        sUt_password1 = qsUserStatus.password1
        sUt_password2 = qsUserStatus.password2
        sUt_password3 = qsUserStatus.password3
        bUt_check_password1 = bUt_check_password2 = bUt_check_password3 = False
        if sUt_password1 is not None:
            bUt_check_password1 = check_password(new_password, sUt_password1)
        if sUt_password2 is not None:
            bUt_check_password2 = check_password(new_password, sUt_password2)
        if sUt_password3 is not None:
            bUt_check_password3 = check_password(new_password, sUt_password3)
        if bUt_check_password3 or bUt_check_password2 or bUt_check_password1:
            error = "密碼與前三次歷史紀錄重複"
            return False, error
        return True, error


@login_required
def userlist(request):
    objMenugroups = menugroup.objects.all()
    context = {
        "objMenugroup": objMenugroups,
    }
    return render(request, "accounts/userlist.html", context)

@login_required
def auth_group_list(request):
    """ 群組人員權限管理 """
    qsPermission = Permission.objects.select_related("content_type").filter(content_type__app_label__in=['auth', 'file_manager', 'pointers']).order_by("id")
    qaUser = User.objects.filter()
    objParameter = parameter.objects.filter(pa_key='指標分類').order_by('pa_sort')

    context = {
        "Permissions": qsPermission,
        "Users": qaUser,
        "objParameter": objParameter,
    }

    return render(request, 'accounts/auth_group_list.html', context)


@login_required
def auth_groupobject_list(request):
    """ 群組指標權限管理 """
    qaUser = User.objects.filter()
    objParameter = parameter.objects.filter(pa_key='指標分類').order_by('pa_sort')

    context = {
        "Users": qaUser,
        "objParameter": objParameter,
    }

    return render(request, 'accounts/auth_groupobject_list.html', context)


def generate_password_reset_token(user):
    """產生重設密碼的驗證碼"""
    token = shortuuid.random(length=8)  # 生成 8 字元 token
    PasswordResetToken.objects.create(user=user, token=token)
    return token


def generate_email_otp(email: str, at_time: int | None = None) -> str:
    """產生 Email OTP 驗證碼"""
    OTP_LENGTH = 6
    OTP_STEP_SECONDS = 300  # 5 分鐘

    if at_time is None:
        at_time = int(time.time())

    key = email.encode("utf-8")
    timestep = at_time // OTP_STEP_SECONDS

    hmac_object = hmac.new(key, timestep.to_bytes(8, "big"), hashlib.sha1)
    hmac_sha1 = hmac_object.hexdigest()

    offset = int(hmac_sha1[-1], 16)
    binary = int(hmac_sha1[offset * 2 : (offset * 2) + 8], 16) & 0x7FFFFFFF
    print(str(binary)[-OTP_LENGTH:])

    return str(binary)[-OTP_LENGTH:]

