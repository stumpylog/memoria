"""
URL configuration for memoria project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from memoria.views import AlbumsView
from memoria.views import DatesView
from memoria.views import HomePageView
from memoria.views import ImagesView
from memoria.views import LocationsView
from memoria.views import PeopleView
from memoria.views import ProfileView
from memoria.views import SettingsView
from memoria.views import SourcesView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="home")),
    path("home/", HomePageView.as_view(), name="home"),
    path("images/", ImagesView.as_view(), name="images"),
    path("sources/", SourcesView.as_view(), name="sources"),
    path("albums/", AlbumsView.as_view(), name="albums"),
    path("people/", PeopleView.as_view(), name="people"),
    path("locations/", LocationsView.as_view(), name="locations"),
    path("dates/", DatesView.as_view(), name="dates"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("settings/", SettingsView.as_view(), name="settings"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html.jinja"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="logout.html.jinja"), name="logout"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(template_name="password_reset.html.jinja"),
        name="password_reset",
    ),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
