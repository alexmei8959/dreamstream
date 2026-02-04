import uuid
from django.db import models
from Dreamstream.model_manager import UanModel, UanModelManager


# Create your models here.

# 參數檔
class parameter(UanModel, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text='uuid')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='建立日期', help_text='建立日期')
    create_user = models.CharField(max_length=50, null=False, verbose_name='建立者', help_text='建立者')
    last_modified_date = models.DateTimeField(auto_now=True, verbose_name='修改日期', help_text='修改日期')
    last_modified_user = models.CharField(max_length=50, null=False, verbose_name='修改者', help_text='修改者')

    pa_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='參數類別', help_text='參數類別')
    pa_key = models.CharField(max_length=50, null=False, verbose_name='參數名稱', help_text='參數名稱')
    pa_value = models.CharField(max_length=500, null=False, verbose_name='參數值', help_text='參數值')
    pa_sort = models.SmallIntegerField(null=True, verbose_name='排序', help_text='排序')
    pa_comment = models.CharField(max_length=100, null=True, blank=True, verbose_name='備註', help_text='備註')

    class Meta:
        verbose_name = '參數檔'

    def __str__(self):
        return self.pa_key

    objects = UanModelManager()


# 選單檔
class menu(UanModel, models.Model):
    """ sidebar選單設定 """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text='uuid')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='建立日期', help_text='建立日期')
    create_user = models.CharField(max_length=50, null=False, verbose_name='建立者', help_text='建立者')
    last_modified_date = models.DateTimeField(auto_now=True, verbose_name='修改日期', help_text='修改日期')
    last_modified_user = models.CharField(max_length=50, null=False, verbose_name='修改者', help_text='修改者')

    menu_1st = models.CharField(max_length=128, null=False, verbose_name='主選單名稱', help_text='主選單名稱')
    menu_1st_icon = models.CharField(max_length=128, null=False, verbose_name='主選單icon', help_text='主選單icon')
    menu_1st_sort = models.SmallIntegerField(null=True, blank=True, verbose_name='主選單排序', help_text='主選單排序')
    menu_2st = models.CharField(max_length=128, null=True, blank=True, verbose_name='次選單名稱', help_text='次選單名稱')
    menu_2st_url = models.CharField(max_length=128, null=True, blank=True, verbose_name='選單url', help_text='選單url')
    menu_2st_sort = models.SmallIntegerField(null=True, blank=True, verbose_name='次選單排序', help_text='次選單排序')

    class Meta:
        verbose_name = '選單檔'

    def __str__(self):
        return self.menu_1st

    objects = UanModelManager()


# 選單群組檔
class menugroup(UanModel, models.Model):
    """ sidebar選單群組設定 """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text='uuid')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='建立日期', help_text='建立日期')
    create_user = models.CharField(max_length=50, null=False, verbose_name='建立者', help_text='建立者')
    last_modified_date = models.DateTimeField(auto_now=True, verbose_name='修改日期', help_text='修改日期')
    last_modified_user = models.CharField(max_length=50, null=False, verbose_name='修改者', help_text='修改者')

    menu_group = models.CharField(max_length=128, null=False, verbose_name='群組名稱', help_text='群組名稱')
    menu_id = models.JSONField(null=True, blank=True, verbose_name='群組代碼', help_text='群組代碼')

    class Meta:
        verbose_name = '選單群組檔'

    def __str__(self):
        return self.menu_group

    objects = UanModelManager()
