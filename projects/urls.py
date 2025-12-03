from django.urls import path
from .views import ProjectListCreateView, ProjectDetailView, ProjectMemberListCreateView, ProjectMemberDetailView

urlpatterns = [
    path("", ProjectListCreateView.as_view(), name="project-list-create"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("<int:project_id>/members/", ProjectMemberListCreateView.as_view(), name="project-members"),
    path("<int:project_id>/members/<int:pk>/", ProjectMemberDetailView.as_view(), name="project-member-detail"),

]