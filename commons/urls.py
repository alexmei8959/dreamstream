from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, viewsets

app_name = "commons"

router = DefaultRouter()
router.register(r"parameter", viewsets.ParameterViewSet, basename="_parameter")
router.register(r"menu", viewsets.MenuViewSet, basename="_menu")
router.register(r"menugroup", viewsets.MenuGroupViewSet, basename="_menugroup")
urlpatterns = [
    path("", include(router.urls)),
    path("parameter_list/", views.parameterlist, name="parameter-list"),  # 參數管理
    path("menu_list/", views.menulist, name="menu-list"),  # 選單管理
    path("menugroup_list/", views.menugrouplist, name="menugroup-list"),  # 選單群組管理
]
