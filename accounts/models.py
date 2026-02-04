from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from datetime import timedelta
from commons.models import menugroup
from . import app_settings

# Create your models here.
User = get_user_model()

# 定義avatar上傳路徑
def user_avatar_path(instance, filename):
    """
    文件將上傳到 MEDIA_ROOT/avatars/<user_id>/<filename>
    instance: userprofile 模型的一個實例
    filename: 用戶上傳的原始文件名
    """
    # 確保 instance.user 不是 None 並且 instance.user.id 存在
    # 在模型保存之前，相關的 User 對象應該已經存在並具有 ID
    if instance.user and instance.user.id:
        return f'avatars/{instance.user.id}/{filename}'
    # 提供一個備用路徑，以防 user 或 user.id 不可用 (雖然 ForeignKey 通常會確保 user 存在)
    # 或者拋出一個錯誤，如果這是不可接受的情況
    return f'avatars/unknown_user/{filename}'


class userstatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_lock = models.BooleanField(default=False, verbose_name='帳號是否鎖定', help_text='帳號是否鎖定')
    lock_date = models.DateTimeField(null=True, verbose_name='銷定時間', help_text='銷定時間')
    is_resetpwd = models.BooleanField(default=False, verbose_name='密碼是否需要重設', help_text='密碼是否需要重設')
    loginfail_times = models.SmallIntegerField(default=0, verbose_name='密碼是否需要重設', help_text='密碼是否需要重設')
    password1 = models.CharField(max_length=128, null=True, blank=True, verbose_name='前一次密碼', help_text='前一次密碼')
    password2 = models.CharField(max_length=128, null=True, blank=True, verbose_name='前二次密碼', help_text='前二次密碼')
    password3 = models.CharField(max_length=128, null=True, blank=True, verbose_name='前三次密碼', help_text='前三次密碼')
    menugroup = models.ForeignKey(menugroup, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='選單群組', help_text='選單群組')

    class Meta:
        verbose_name = '使用者狀態'


# 使用者資料
class userprofile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role_id = models.IntegerField(null=True, blank=True, verbose_name='角色', help_text='角色，0:總管理者、1:管理者、2:可讀寫使用者、3:唯讀使用者')
    sex = models.CharField(max_length=1, null=True, blank=True, help_text='性別')
    phone = models.CharField(max_length=50, null=True, blank=True, help_text='電話')
    avatar = models.ImageField(upload_to=user_avatar_path, null=True, blank=True, verbose_name='頭像', help_text='頭像')
    is_otp = models.BooleanField(default=True, verbose_name='是否啟用OTP', help_text='是否啟用OTP')

    class Meta:
        verbose_name = '使用者資料'



class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=16, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(minutes=app_settings.PASSWORD_RESET_EMAIL_EXPIRE_MIN)
