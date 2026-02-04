from rest_framework import serializers
from commons.models import parameter, menugroup, menu


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = parameter
        fields = "__all__"


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = menu
        fields = "__all__"


class MenuGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = menugroup
        fields = "__all__"
