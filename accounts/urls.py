from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from . import views, viewsets

app_name = "accounts"

router = DefaultRouter()
router.register(r"users", viewsets.userViewSet)
router.register(r'permission', viewsets.permissionViewSet, basename="_permission")
router.register(r'group', viewsets.groupViewSet, basename="_group")
urlpatterns = [
    path("", include(router.urls)),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", NormalLogoutView.as_view(), name="logout"),
    path(
        "change_password/", ChangePasswordView.as_view(), name="change_password"
    ),  # 變更密碼
    path("user_list/", views.userlist, name="user-list"),  # 使用者管理
    path('auth_group_list/', views.auth_group_list, name='auth_group-list'),  # 群組人員權限管理
    path('auth_groupobject_list/', views.auth_groupobject_list, name='auth_groupobject-list'),  # 群組指標權限管理
]
