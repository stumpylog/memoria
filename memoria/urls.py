"""
URL configuration for memoria project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from memoria import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="home")),
    path("home/", views.HomePageView.as_view(), name="home"),
    path("images/", views.ImagesView.as_view(), name="images"),
    path("sources/", views.SourcesView.as_view(), name="sources"),
    path("albums/", views.AlbumsView.as_view(), name="albums"),
    path("people/", views.PeopleView.as_view(), name="people"),
    path("locations/", views.LocationsView.as_view(), name="locations"),
    path("dates/", views.DatesView.as_view(), name="dates"),
    #
    # User Profile
    #
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/update-email/", views.UpdateEmailView.as_view(), name="profile_update_email"),
    path("profile/update-profile/", views.UpdateProfileView.as_view(), name="profile_update_details"),
    path("profile/manage-groups/", views.ManageGroupsView.as_view(), name="profile_manage_groups"),
    #
    # Admin Settings
    #
    path("settings/", views.AdminSettingsView.as_view(), name="settings"),
    path("settings/users/add/", views.AddUserView.as_view(), name="admin_add_user"),
    path(
        "settings/users/<int:pk>/toggle-active/",
        views.ToggleUserActiveView.as_view(),
        name="admin_toggle_user_active",
    ),
    path(
        "settings/users/<int:pk>/manage-groups/",
        views.ManageUserGroupsView.as_view(),
        name="admin_manage_user_groups",
    ),
    path("settings/groups/add/", views.AddGroupView.as_view(), name="admin_add_group"),
    path("settings/groups/<int:pk>/remove/", views.RemoveGroupView.as_view(), name="admin_remove_group"),
    #
    # Authentication
    #
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html.jinja"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="auth/logout.html.jinja"), name="logout"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html.jinja"),
        name="password_reset",
    ),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
