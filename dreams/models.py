import uuid
from django.db import models
from django.contrib.auth import get_user_model
from Dreamstream.model_manager import UanModel, UanModelManager

# Create your models here.
User = get_user_model()


# 夢境檔
class dream(UanModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text='uuid')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='建立日期', help_text='建立日期')
    create_user = models.CharField(max_length=50, null=False, verbose_name='建立者', help_text='建立者')
    last_modified_date = models.DateTimeField(auto_now=True, verbose_name='修改日期', help_text='修改日期')
    last_modified_user = models.CharField(max_length=50, null=False, verbose_name='修改者', help_text='修改者')

    title = models.CharField(max_length=120, verbose_name="標題")
    parent = models.ForeignKey(
        "self", null=True, blank=True,
        related_name="children",
        on_delete=models.CASCADE,
        db_index=True,
    )
    is_folder = models.BooleanField(default=False, verbose_name="是否資料夾")

    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='dreams')
    dream_date = models.DateField(null=True, blank=True, verbose_name='做夢的日期', help_text='做夢的日期')
    dream_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='類別', help_text='類別')
    dream_content = models.JSONField(null=True, blank=True, verbose_name='夢的內容', help_text='夢的內容')
    dream_reviewer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='審核者', help_text='審核者', related_name='dreams_reviewed')
    dream_review_date = models.DateTimeField(null=True, blank=True, verbose_name='審核日期', help_text='審核日期')

    class Meta:
        verbose_name = '夢境檔'

    objects = UanModelManager()


# 夢境回應檔
class dream_reply(UanModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text='uuid')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='建立日期', help_text='建立日期')
    create_user = models.CharField(max_length=50, null=False, verbose_name='建立者', help_text='建立者')
    last_modified_date = models.DateTimeField(auto_now=True, verbose_name='修改日期', help_text='修改日期')
    last_modified_user = models.CharField(max_length=50, null=False, verbose_name='修改者', help_text='修改者')

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    dream = models.ForeignKey(dream, null=False, on_delete=models.CASCADE, related_name='replies')
    reply_date = models.DateTimeField(null=False, verbose_name='回應的日期', help_text='回應的日期')
    reply_content = models.JSONField(null=False, verbose_name='回應的內容', help_text='回應的內容')

    class Meta:
        verbose_name = '夢境回應檔'

    objects = UanModelManager()
