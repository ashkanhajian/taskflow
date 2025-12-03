from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Project, ProjectsMember

User = get_user_model()

class ProjectsMemberSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProjectsMember
        fields = '__all__'
        read_only_fields = ('user','id','role','joined_at')

class ProjectSerializer(serializers.ModelSerializer):
    owner= serializers.ReadOnlyField(source='owner.username')
    members = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('owner','id','created_at','updated_at')
    def get_members(self, obj):
        memberships = obj.members.select_related('user')
        return ProjectsMemberSerializer(memberships, many=True).data


class ProjectMemberWriteSerializer(serializers.ModelSerializer):

    username = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=ProjectsMember.Role.choices)

    class Meta:
        model = ProjectsMember
        fields = ("id", "username", "role", "project", "joined_at")
        read_only_fields = ("id", "project", "joined_at")

    def validate(self, attrs):
        username = attrs.get("username")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "کاربری با این نام پیدا نشد."})

        attrs["user"] = user
        return attrs