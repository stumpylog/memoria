"""
URL configuration for memoria project.
"""

import json

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from memoria import views


@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Return CSRF token for the frontend to use in requests
    """
    token = get_token(request)
    return JsonResponse({"csrfToken": token})


@require_POST
def login_view(request):
    """
    Handle user login
    """
    data = json.loads(request.body)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"message": "Please provide both username and password"}, status=400)

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return JsonResponse(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                    # Add any other user fields you need
                },
            },
        )
    return JsonResponse({"message": "Invalid credentials. Please try again."}, status=401)


@require_POST
def logout_view(request):
    """
    Handle user logout
    """
    logout(request)
    return JsonResponse({"message": "Logged out successfully"})


@login_required
def user_info(request):
    """
    Return current user info
    """
    user = request.user
    return JsonResponse(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            # Add any other user fields you need
        },
    )


urlpatterns = [
    # path("", RedirectView.as_view(pattern_name="home")),
    path("api/csrf/", get_csrf_token, name="csrf"),
    path("api/login/", login_view, name="login"),
    path("api/logout/", logout_view, name="logout"),
    path("api/user/", user_info, name="user_info"),
    path("home/", views.HomePageView.as_view(), name="home"),
    #
    # Images
    #
    path("images/", views.ImageListView.as_view(), name="image_list"),
    path("images/<int:pk>/", views.ImageDetailView.as_view(), name="image_detail"),
    path("images/<int:pk>/edit/", views.ImageUpdateView.as_view(), name="image_update"),
    path("ajax/get_subdivisions/", views.ajax_get_subdivisions, name="ajax_get_subdivisions"),
    path("ajax/get_cities/", views.ajax_get_cities, name="ajax_get_cities"),
    path("ajax/get_sub_locations/", views.ajax_get_sub_locations, name="ajax_get_sub_locations"),
    path("folders/", views.ImageFolderListView.as_view(), name="image_folder_list"),
    path("folders/<int:pk>/", views.ImageFolderDetailView.as_view(), name="image_folder_detail"),
    path("albums/", views.AlbumsView.as_view(), name="albums"),
    #
    # Person related
    #
    path("people/", views.PeopleListView.as_view(), name="people_list"),
    path("people/<int:pk>/", views.PersonDetailView.as_view(), name="person_detail"),
    path("people/<int:pk>/photos/", views.PersonPhotosListView.as_view(), name="person_photos"),
    path("locations/", views.RoughLocationListView.as_view(), name="locations"),
    path("locations/<int:pk>/", views.RoughLocationDetailView.as_view(), name="location_detail"),
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
