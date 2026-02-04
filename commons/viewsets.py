import base64
import json

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from model_utils import Choices

from .models import parameter, menugroup, menu
from .serializers import (
    ParameterSerializer,
    MenuGroupSerializer,
    MenuSerializer,
)


class ParameterViewSet(viewsets.ModelViewSet):
    queryset = parameter.objects.all()
    serializer_class = ParameterSerializer

    # CRUD要加此段
    def list(self, request, **kwargs) -> dict or None:
        try:
            dParameter = self.__query_by_args(**request.query_params)
            serializer = ParameterSerializer(dParameter["items"], many=True)
            result = dict()
            result["data"] = serializer.data
            result["draw"] = dParameter["draw"]
            result["recordsTotal"] = dParameter["total"]
            result["recordsFiltered"] = dParameter["count"]
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
            ("0", "pa_type"),
            ("1", "pa_key"),
            ("2", "pa_value"),
            ("3", "pa_sort"),
            ("4", "pa_comment"),
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

        # Mutiple column order
        order_column_1 = ""
        if (kwargs.get("order[1][column]", None)) is not None:
            order_column_1 = kwargs.get("order[1][column]", None)[0]
            order_column_1 = ORDER_COLUMN_CHOICES[order_column_1]
            order_1 = kwargs.get("order[1][dir]", None)[0]
            if order_1 == "desc":
                order_column_1 = "-" + order_column_1

        queryset = parameter.objects.all()
        total = queryset.count()

        if search_value:
            queryset = queryset.filter(
                Q(pa_type__icontains=search_value)
                | Q(pa_key__icontains=search_value)
                | Q(pa_value__icontains=search_value)
                | Q(pa_comment__icontains=search_value)
            )

        count = queryset.count()
        if (kwargs.get("order[1][column]", None)) is None:
            queryset = queryset.order_by(order_column)[start : start + length]
        else:
            queryset = queryset.order_by(order_column, order_column_1)[
                start : start + length
            ]
        return {"items": queryset, "count": count, "total": total, "draw": draw}


class MenuViewSet(viewsets.ModelViewSet):
    queryset = menu.objects.all()
    serializer_class = MenuSerializer

    def __query_by_args(self, **kwargs) -> dict:
        ORDER_COLUMN_CHOICES = Choices(
            ("0", "create_date"),
            ("1", "menu_1st"),
            ("2", "menu_1st_sort"),
            ("3", "menu_2st"),
            ("4", "menu_2st_url"),
            ("5", "menu_2st_sort"),
        )

        draw: int = int(kwargs.get("draw", None)[0])
        length: int = int(kwargs.get("length", None)[0])
        start: int = int(kwargs.get("start", None)[0])
        search_value: str = kwargs.get("search[value]", None)[0]

        # 處理排序條件
        orders = []
        i = 0
        while True:
            column_key: str = f"order[{i}][column]"
            dir_key: str = f"order[{i}][dir]"

            # 確保取出值並處理為單一字串
            order_column_list: list = kwargs.get(column_key)
            order_dir_list: list = kwargs.get(dir_key)

            # 如果無法取到值，結束迴圈
            if not order_column_list or not order_dir_list:
                break

            # 處理 list，只取第一個值
            order_column: str = (
                order_column_list[0]
                if isinstance(order_column_list, list)
                else order_column_list
            )
            order_dir: str = (
                order_dir_list[0]
                if isinstance(order_dir_list, list)
                else order_dir_list
            )

            # 映射欄位名稱
            mapped_column: str = ORDER_COLUMN_CHOICES[order_column]
            if not mapped_column:
                raise ValueError(f"Invalid order column: {order_column}")

            # 設定排序方向
            if order_dir == "desc":
                mapped_column = f"-{mapped_column}"

            orders.append(mapped_column)
            i += 1

        queryset = self.queryset

        # datatable搜尋關鍵字
        if search_value:
            queryset = queryset.filter(
                Q(menu_1st__icontains=search_value)
                | Q(menu_1st_icon__icontains=search_value)
                | Q(menu_1st_sort__icontains=search_value)
                | Q(menu_2st__icontains=search_value)
                | Q(menu_2st_url__icontains=search_value)
                | Q(menu_2st_sort__icontains=search_value)
            )

        # 取出queryset總數量
        total: int = queryset.count()
        count: int = queryset.count()

        # 根據datatable要求數量篩選
        queryset = queryset.order_by(*orders)[start : start + length]

        return {"items": queryset, "count": count, "total": total, "draw": draw}

    def list(self, request, **kwargs) -> dict or None:
        try:
            dMenu = self.__query_by_args(**request.query_params)
            serializer = self.serializer_class(dMenu["items"], many=True)
            # 資料結構重新排列
            result = dict()
            result["data"] = serializer.data
            result["draw"] = dMenu["draw"]
            result["recordsTotal"] = dMenu["total"]
            result["recordsFiltered"] = dMenu["count"]
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

    def create(self, request, **kwargs) -> dict or None:
        form_raw_data = request.data
        __serializer = self.serializer_class(data=form_raw_data)
        try:
            if __serializer.is_valid():
                __serializer.save()

                return Response(__serializer.data, status=status.HTTP_201_CREATED)
            else:
                # 返回驗證錯誤
                print(__serializer.errors)
                return Response(__serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class MenuGroupViewSet(viewsets.ModelViewSet):
    queryset = menugroup.objects.all()
    serializer_class = MenuGroupSerializer

    def __query_by_args(self, **kwargs) -> dict:
        ORDER_COLUMN_CHOICES = Choices(
            ("0", "create_date"),
            ("1", "menu_group"),
        )

        draw: int = int(kwargs.get("draw", None)[0])
        length: int = int(kwargs.get("length", None)[0])
        start: int = int(kwargs.get("start", None)[0])
        search_value: str = kwargs.get("search[value]", None)[0]

        # 處理排序條件
        orders = []
        i = 0
        while True:
            column_key: str = f"order[{i}][column]"
            dir_key: str = f"order[{i}][dir]"

            # 確保取出值並處理為單一字串
            order_column_list: list = kwargs.get(column_key)
            order_dir_list: list = kwargs.get(dir_key)

            # 如果無法取到值，結束迴圈
            if not order_column_list or not order_dir_list:
                break

            # 處理 list，只取第一個值
            order_column: str = (
                order_column_list[0]
                if isinstance(order_column_list, list)
                else order_column_list
            )
            order_dir: str = (
                order_dir_list[0]
                if isinstance(order_dir_list, list)
                else order_dir_list
            )

            # 映射欄位名稱
            mapped_column: str = ORDER_COLUMN_CHOICES[order_column]
            if not mapped_column:
                raise ValueError(f"Invalid order column: {order_column}")

            # 設定排序方向
            if order_dir == "desc":
                mapped_column = f"-{mapped_column}"

            orders.append(mapped_column)
            i += 1

        queryset = self.queryset

        # datatable搜尋關鍵字
        if search_value:
            queryset = queryset.filter(Q(menu_group__icontains=search_value))

        # 取出queryset總數量
        total: int = queryset.count()
        count: int = queryset.count()

        # 根據datatable要求數量篩選
        queryset = queryset.order_by(*orders)[start : start + length]

        return {"items": queryset, "count": count, "total": total, "draw": draw}

    def list(self, request, **kwargs) -> dict or None:
        try:
            dMenuGroup = self.__query_by_args(**request.query_params)
            __serializer = self.serializer_class(dMenuGroup["items"], many=True)
            # 資料結構重新排列
            result = dict()
            result["data"] = __serializer.data
            result["draw"] = dMenuGroup["draw"]
            result["recordsTotal"] = dMenuGroup["total"]
            result["recordsFiltered"] = dMenuGroup["count"]
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

    def create(self, request, **kwargs) -> dict or None:
        data = request.data.copy()
        __serializer = self.serializer_class(data=data)
        try:
            if __serializer.is_valid():
                __serializer.save()

                return Response(__serializer.data, status=status.HTTP_201_CREATED)
            else:
                # 返回驗證錯誤
                print(__serializer.errors)
                return Response(__serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)
