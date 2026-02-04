from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from django.contrib.auth.models import User, Permission, Group
from accounts.models import userstatus
from commons.serializers import MenuGroupSerializer


class userstatusSerializer(serializers.ModelSerializer):
    menugroup = MenuGroupSerializer(read_only=True)

    class Meta:
        model = userstatus
        fields = '__all__'


class userSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    last_login = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    userstatus = userstatusSerializer(many=True, source='userstatus_set', read_only=True)

    class Meta:
        model = User
        # fields = '__all__'
        fields = ('id', 'username', 'password', 'first_name', 'email', 'is_superuser', 'is_staff', 'is_active', 'date_joined', 'last_login', 'userstatus')

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = "__all__"

class PermissionSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(read_only=True)

    class Meta:
        model = Permission
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    users = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'users']

    def get_users(self, obj):
        return [{'id': u.id, 'first_name': u.first_name, 'email': u.email} for u in obj.user_set.all()]