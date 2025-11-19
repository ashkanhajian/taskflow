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