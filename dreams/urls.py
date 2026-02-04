from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, viewsets

app_name = "dreams"

router = DefaultRouter()
urlpatterns = [
    path("", include(router.urls)),
    path("dream_list/", views.dreamlist, name="dream-list"),  # 夢境管理
    path("dream_reply/", views.dream_reply, name="dream-reply"),  # 夢境回應
]
