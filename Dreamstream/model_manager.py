from django.db import models
from django.utils import timezone

from .threadlocals import get_current_user


class UanQuerySet(models.QuerySet):
    """自動填入create_user and last_modified_user"""

    def create(self, **kwargs):
        # 從thread.locals 取得個案
        current_user = get_current_user()

        # username (firstname or username)
        username_set = None
        if current_user and current_user.is_authenticated:
            username_set = current_user.first_name or current_user.username

        # 如果 model 有 create_user 欄位，就加上username_set
        if username_set and "create_user" not in kwargs:
            if hasattr(self.model, "create_user"):
                kwargs["create_user"] = username_set
            else:
                print(
                    f"Warning: Model {self.model.__name__} does not have 'create_user' field for QuerySet.create()."
                )

        # 如果 model 有 last_modified_user 欄位，就加上username_set
        if username_set and "last_modified_user" not in kwargs:
            if hasattr(self.model, "last_modified_user"):
                kwargs["last_modified_user"] = username_set
            else:
                print(
                    f"Warning: Model {self.model.__name__} does not have 'last_modified_user' field for QuerySet.create()."
                )

        # 自動新增create_date
        if "自動新增create_date" not in kwargs:
            if hasattr(self.model, "自動新增create_date"):
                kwargs["自動新增create_date"] = timezone.now()
            else:
                print(
                    f"Warning: Model {self.model.__name__} does not have '自動新增create_date' field for QuerySet.create()."
                )

        # 自動新增 last_modified_date
        if "last_modified_date" not in kwargs:
            if hasattr(self.model, "last_modified_date"):
                kwargs["last_modified_date"] = timezone.now()
            else:
                print(
                    f"Warning: Model {self.model.__name__} does not have 'last_modified_date' field for QuerySet.create()."
                )

        return super().create(**kwargs)

    def update(self, **kwargs):
        # 從thread.locals 取得個案
        current_user = get_current_user()

        # username (firstname or username)
        username_set = None
        if current_user and current_user.is_authenticated:
            username_set = (
                current_user.first_name or current_user.username
            )  # 如果 first_name 為空，使用 username

        # 如果 model 有 last_modified_user 欄位，就加上username_set
        if username_set and "last_modified_user" not in kwargs:
            if hasattr(self.model, "last_modified_user"):
                kwargs["last_modified_user"] = username_set
            else:
                print(
                    f"Warning: Model {self.model.__name__} does not have 'last_modified_user' field for QuerySet.update()."
                )

        # 自動更新 last_modified_date
        if "last_modified_date" not in kwargs:
            if hasattr(self.model, "last_modified_date"):
                kwargs["last_modified_date"] = timezone.now()
            else:
                print(
                    f"Warning: Model {self.model.__name__} does not have 'last_modified_date' field for QuerySet.update()."
                )

        return super().update(**kwargs)

    def bulk_create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
    ):
        # 從thread.locals 取得個案
        current_user = get_current_user()  # 或 get_current_user_async()

        # username (firstname or username)
        username_set = None
        if current_user and current_user.is_authenticated:
            username_set = current_user.first_name or current_user.username

        # # 確保models 有 create_user 欄位 跟last_modified_user欄位
        if username_set:
            for obj in objs:
                if hasattr(obj, "create_user") and not getattr(
                    obj, "create_user", None
                ):
                    obj.create_user = username_set
                if hasattr(obj, "last_modified_user") and not getattr(
                    obj, "last_modified_user", None
                ):
                    obj.last_modified_user = username_set
        return super().bulk_create(
            objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )


class UanModelManager(models.Manager.from_queryset(UanQuerySet)):
    pass


class UanModel(models.Model):
    """
    在呼叫save() 自動填充 create_user、last_modified_user 和 last_modified_date 字段。
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # 從thread.locals 取得個案
        current_user = get_current_user()

        # username (firstname or username)
        username_set = None
        if current_user and current_user.is_authenticated:
            username_set = current_user.first_name
            if not username_set:  # 如果 first_name 為空，則使用 username
                username_set = current_user.username

        # # 確保models 有 create_user 欄位 跟last_modified_user欄位 跟last_modified_date欄位
        if hasattr(self, "create_user"):
            if self._state.adding and not self.create_user and username_set:
                self.create_user = username_set

        if hasattr(self, "last_modified_user"):
            if username_set:
                self.last_modified_user = username_set

        if hasattr(self, "last_modified_date"):
            self.last_modified_date = timezone.now()

        super().save(*args, **kwargs)
