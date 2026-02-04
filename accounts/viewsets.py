from django.contrib.auth.models import Permission, Group
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from guardian.shortcuts import assign_perm, remove_perm, get_perms
from model_utils import Choices
from .models import User, userstatus
from .serializers import userSerializer, userstatusSerializer, GroupSerializer, PermissionSerializer
import json


class userViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = userSerializer

    # CRUD要加此段
    def list(self, request, **kwargs):
        try:
            users = self.__query_by_args(**request.query_params)
            serializer = userSerializer(users["items"], many=True)
            result = dict()
            result["data"] = serializer.data
            # result['data'] = result['data'].order_by('last_login')
            result["draw"] = users["draw"]
            result["recordsTotal"] = users["total"]
            result["recordsFiltered"] = users["count"]
            return Response(
                result, status=status.HTTP_200_OK, template_name=None, content_type=None
            )

        except Exception as e:
            return Response(
                e,
                status=status.HTTP_404_NOT_FOUND,
                template_name=None,
                content_type=None,
            )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = json.dumps(request.data)
        data = json.loads(data)
        data["password"] = make_password(data["password"])
        try:
            with transaction.atomic():
                _serializer = self.serializer_class(data=data)
                if _serializer.is_valid():
                    _serializer.save()

                    # join userstatus
                    user = User.objects.filter(username=data["username"]).get()
                    userstatus.objects.create(
                        user=user,
                        password1=user.password,
                        department_id=data["department_id"],
                        menugroup_id = data["menugroup_id"]
                    )  # 改直接存檔

                    relations = []
                    # 如果 user 是 subordinate，補上新部門的主管
                    if data["is_staff"] == "0":
                        dept_managers = User.objects.filter(
                            is_staff=True,
                            userstatus__department_id=data["department_id"]
                        )
                        relations = [userrelation(manager=manager, subordinate=user) for manager in dept_managers]
                    elif data["is_staff"] == "1":
                        # 如果 user 是主管，補上下屬關係
                        dept_subordinates = User.objects.filter(
                            is_staff=False,
                            userstatus__department_id=data["department_id"]
                        )
                        relations += [userrelation(manager=user, subordinate=sub) for sub in dept_subordinates]

                    # 批次建立
                    if relations:
                        userrelation.objects.bulk_create(relations)

                    return Response(
                        data=_serializer.data, status=status.HTTP_201_CREATED
                    )  # NOQA
                else:
                    return Response(
                        data=_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )  # NOQA
        except Exception as e:
            # 需檢查電話號碼或email是否已存在
            str_e = str(e)
            if "unique" in str_e:
                error_msg = "此Email已存在!"
            else:
                error_msg = str_e
            return Response(data=error_msg, status=status.HTTP_400_BAD_REQUEST)

    # 改寫Update
    def update(self, request, *args, **kwargs):
        data = json.dumps(request.data)
        data = json.loads(data)
        """
            密碼與前三次歷史紀錄任一個重複都要拒絕存檔
            如果沒有重複就存進DB
            DB欄位有password1、password2、password3，
            檢查欄位有沒有值
            有就換下一個，檢查到沒有值就存檔在該欄位
            當三個欄位都有值：
                1.刪除password3
                2.password1補進password2
                3.password2補進password3，
                4.user.password存進password1
            """
        # join userstatus
        user = User.objects.filter(id=data["user_id"]).get()
        qsUserStatus = userstatus.objects.filter(user=user).first()
        sUt_password1 = qsUserStatus.password1
        sUt_password2 = qsUserStatus.password2
        sUt_password3 = qsUserStatus.password3
        bUt_check_password1 = bUt_check_password2 = bUt_check_password3 = False
        if sUt_password1 is not None:
            bUt_check_password1 = check_password(data["password"], sUt_password1)
        if sUt_password2 is not None:
            bUt_check_password2 = check_password(data["password"], sUt_password2)
        if sUt_password3 is not None:
            bUt_check_password3 = check_password(data["password"], sUt_password3)
        if bUt_check_password3 or bUt_check_password2 or bUt_check_password1:
            return Response(
                data="密碼與前三次歷史紀錄重複", status=status.HTTP_400_BAD_REQUEST
            )

        # 判斷密碼欄位是否有變更
        isPasswordChange = False
        if "pbkdf2" not in str(data["password"]):
            isPasswordChange = True
            data["password"] = make_password(data["password"])

        try:
            instance = self.get_object()
            _serializer = self.serializer_class(instance, data=data)

            with transaction.atomic():
                if _serializer.is_valid():
                    _serializer.save()
                    # 變更密碼時要記錄前三次密碼
                    if isPasswordChange:
                        qsUserStatus.password3 = qsUserStatus.password2
                        qsUserStatus.password2 = qsUserStatus.password1
                        qsUserStatus.password1 = user.password
                    qsUserStatus.department_id = data["department_id"]
                    qsUserStatus.menugroup_id = data["menugroup_id"]
                    qsUserStatus.save()

                    # 清除舊關係
                    userrelation.objects.filter(
                        Q(subordinate=user) | Q(manager=user)
                    ).delete()

                    relations = []
                    # 如果 user 是 subordinate，補上新部門的主管
                    if data["is_staff"] == "0":
                        dept_managers = User.objects.filter(
                            is_staff=True,
                            userstatus__department_id=data["department_id"]
                        )
                        relations = [userrelation(manager=manager, subordinate=user) for manager in dept_managers]
                    elif data["is_staff"] == "1":
                        # 如果 user 是主管，補上下屬關係
                        dept_subordinates = User.objects.filter(
                            is_staff=False,
                            userstatus__department_id=data["department_id"]
                        )
                        relations += [userrelation(manager=user, subordinate=sub) for sub in dept_subordinates]

                    # 批次建立
                    if relations:
                        userrelation.objects.bulk_create(relations)

                    return Response(
                        data=_serializer.data, status=status.HTTP_201_CREATED
                    )

        except Exception as e:
            # 需檢查電話號碼或email是否已存在
            str_e = str(e)
            if "Duplicate" in str_e:
                error_msg = "此電話號碼或Email已存在!"
            else:
                error_msg = str_e
            return Response(data=error_msg, status=status.HTTP_400_BAD_REQUEST)

    def __query_by_args(self, **kwargs):
        ORDER_COLUMN_CHOICES = Choices(
            ("0", "id"),
            ("1", "username"),
            ("2", "password"),
            ("3", "first_name"),
            ("4", "email"),
            ("6", "is_active"),
            ("7", "last_login"),
            ("9", "is_staff"),
        )
        draw: int = int(kwargs.get("draw", None)[0])
        length: int = int(kwargs.get("length", None)[0])
        start: int = int(kwargs.get("start", None)[0])
        search_value: str = kwargs.get("search[value]", None)[0]
        order_column: str = kwargs.get("order[0][column]", None)[0]
        order: str = kwargs.get("order[0][dir]", None)[0]

        order_column = ORDER_COLUMN_CHOICES[order_column]
        # django orm '-' -> desc
        if order == "desc":
            order_column = "-" + order_column

        queryset = User.objects.filter(~Q(username="admin")).prefetch_related("userstatus_set")
        total = queryset.count()

        if search_value:
            queryset = queryset.filter(
                Q(username__icontains=search_value)
                | Q(email__icontains=search_value)
                | Q(is_staff__icontains=search_value)
                | Q(is_active__icontains=search_value)
            )

        count = queryset.count()
        queryset = queryset.order_by(order_column)[start : start + length]
        return {"items": queryset, "count": count, "total": total, "draw": draw}

class permissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

    # CRUD要加此段
    def list(self, request, **kwargs) -> dict or None:
        try:
            dPermission = self.__query_by_args(**request.query_params)
            serializer = PermissionSerializer(dPermission["items"], many=True)
            result = dict()
            result["data"] = serializer.data
            result["draw"] = dPermission["draw"]
            result["recordsTotal"] = dPermission["total"]
            result["recordsFiltered"] = dPermission["count"]
            return Response(
                result, status=status.HTTP_200_OK, template_name=None, content_type=None
            )

        except Exception as e:
            return Response(
                e,
                status=status.HTTP_404_NOT_FOUND,
                template_name=None,
                content_type=None,
            )

    def __query_by_args(self, **kwargs) -> dict:
        ORDER_COLUMN_CHOICES = Choices(
            ("0", "id"),
            ("1", "name"),
            ("2", "content_type_id"),
            ("3", "codename"),
        )

        draw: int = int(kwargs.get("draw", None)[0])
        length: int = int(kwargs.get("length", None)[0])
        start: int = int(kwargs.get("start", None)[0])
        search_value: str = kwargs.get("search[value]", None)[0]
        order_column: str = kwargs.get("order[0][column]", None)[0]
        order: str = kwargs.get("order[0][dir]", None)[0]

        order_column = ORDER_COLUMN_CHOICES[order_column]
        # django orm '-' -> desc
        if order == "desc":
            order_column = "-" + order_column

        queryset = Permission.objects.select_related("content_type").all()

        # datatable搜尋關鍵字
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value)
                | Q(codename__icontains=search_value)
            )

        # 取出queryset總數量
        total: int = queryset.count()
        count: int = queryset.count()

        # 根據datatable要求數量篩選
        queryset = queryset.order_by(order_column)[start:start + length]

        return {"items": queryset, "count": count, "total": total, "draw": draw}


class groupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    # CRUD要加此段
    def list(self, request, **kwargs) -> dict or None:
        try:
            dGroup = self.__query_by_args(**request.query_params)
            serializer = GroupSerializer(dGroup["items"], many=True)
            result = dict()
            result["data"] = serializer.data
            result["draw"] = dGroup["draw"]
            result["recordsTotal"] = dGroup["total"]
            result["recordsFiltered"] = dGroup["count"]
            return Response(
                result, status=status.HTTP_200_OK, template_name=None, content_type=None
            )

        except Exception as e:
            return Response(
                str(e),
                status=status.HTTP_404_NOT_FOUND,
                template_name=None,
                content_type=None,
            )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()

        # 前端透過 jQuery 的 $.param 傳送的陣列，其 key 會是 'permissions[]'
        permission_ids = request.data.getlist('permissions[]')
        if permission_ids:
            # 過濾掉可能存在的空字串並取得 Permission 物件
            permissions = Permission.objects.filter(id__in=[pid for pid in permission_ids if pid])
            group.permissions.set(permissions)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        update_type = request.data.get('update_type')  # 前端傳的參數

        # 若是更新 Pointer 權限，不需要走原本的 serializer 完整 update 流程
        if update_type == "pointer_permissions":
            import json
            # 前端傳來的資料結構預計為 JSON 字串，需解析
            # 格式: [{"id": "uuid", "perms": ["view_pointer", "change_pointer"]}, ...]
            pointers_data = json.loads(request.data.get('pointers_data', '[]'))

            # 定義相關的權限代碼 (app_label.codename)
            # 假設 app_name 為 'pointers'
            perm_map = {
                'view': 'pointers.view_pointer',
                'change': 'pointers.change_pointer',
                'delete': 'pointers.delete_pointer'
            }

            for p_data in pointers_data:
                p_obj = pointer.objects.get(id=p_data['id'])
                target_perms = set(p_data['perms'])  # 前端希望擁有的權限 ['view', 'delete']

                # 目前該群組對該物件擁有的權限
                # get_perms 回傳的是短名 list，如 ['view_pointer', 'change_pointer']
                current_perms_short = set(get_perms(instance, p_obj))

                # 處理 View
                if 'view' in target_perms:
                    if 'view_pointer' not in current_perms_short:
                        assign_perm(perm_map['view'], instance, p_obj)
                else:
                    if 'view_pointer' in current_perms_short:
                        remove_perm(perm_map['view'], instance, p_obj)

                # 處理 Change
                if 'change' in target_perms:
                    if 'change_pointer' not in current_perms_short:
                        assign_perm(perm_map['change'], instance, p_obj)
                else:
                    if 'change_pointer' in current_perms_short:
                        remove_perm(perm_map['change'], instance, p_obj)

                # 處理 Delete
                if 'delete' in target_perms:
                    if 'delete_pointer' not in current_perms_short:
                        assign_perm(perm_map['delete'], instance, p_obj)
                else:
                    if 'delete_pointer' in current_perms_short:
                        remove_perm(perm_map['delete'], instance, p_obj)

            return Response({'status': 'success', 'message': '指標權限更新成功'})

        # 原有的更新邏輯
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()

        # 更新群組權限 (auth_group_permissions)
        if update_type == "permissions":
            permission_ids = request.data.getlist('permissions[]')
            permissions = Permission.objects.filter(id__in=[pid for pid in permission_ids if pid])
            group.permissions.set(permissions)

        # 更新群組人員 (auth_user_groups)
        if update_type == "users":
            user_ids = request.data.getlist('group_users[]')
            users = User.objects.filter(id__in=[uid for uid in user_ids if uid])
            group.user_set.set(users)

        return Response(serializer.data)

    # 新增一個 action 用來獲取特定群組的指標權限列表
    @action(detail=True, methods=['get'])
    def pointer_perms(self, request, pk=None):
        group = self.get_object()
        # 取得所有指標並根據 pointer_code 排序
        pointers = pointer.objects.all().order_by('pointer_code')

        data = []
        for p in pointers:
            # 取得該群組對此物件的所有權限
            # get_perms 回傳 list，例如 ['view_pointer', 'change_pointer']
            perms = get_perms(group, p)

            data.append({
                'id': str(p.id),
                'code': p.pointer_code,
                'name': p.pointer_name,
                'type': p.pointer_type,
                'has_view': 'view_pointer' in perms,
                'has_change': 'change_pointer' in perms,
                'has_delete': 'delete_pointer' in perms,
            })

        return Response(data)

    def __query_by_args(self, **kwargs) -> dict:
        ORDER_COLUMN_CHOICES = Choices(
            ("0", "id"),
            ("1", "name"),
        )

        draw: int = int(kwargs.get("draw", None)[0])
        length: int = int(kwargs.get("length", None)[0])
        start: int = int(kwargs.get("start", None)[0])
        search_value: str = kwargs.get("search[value]", None)[0]
        order_column: str = kwargs.get("order[0][column]", None)[0]
        order: str = kwargs.get("order[0][dir]", None)[0]

        order_column = ORDER_COLUMN_CHOICES[order_column]
        # django orm '-' -> desc
        if order == "desc":
            order_column = "-" + order_column

        queryset = Group.objects.prefetch_related('permissions', 'user_set').all()

        # datatable搜尋關鍵字
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value)
            )

        # 取出queryset總數量
        total: int = queryset.count()
        count: int = queryset.count()

        # 根據datatable要求數量篩選
        queryset = queryset.order_by(order_column)[start:start + length]

        # 這裡轉成 datatable 需要的格式
        items = []
        for group in queryset:
            items.append({
                "id": group.id,
                "name": group.name,
                "users": [
                    {
                        "id": u.id,
                        "username": u.username,
                        "first_name": u.first_name,
                        "email": u.email,
                    }
                    for u in group.user_set.all()
                ]
            })

        return {"items": queryset, "count": count, "total": total, "draw": draw}