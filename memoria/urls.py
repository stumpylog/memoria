"""
URL configuration for memoria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from memoria.views import AlbumsView
from memoria.views import DatesView
from memoria.views import GalleriesView
from memoria.views import HomePageView
from memoria.views import LocationsView
from memoria.views import PeopleView
from memoria.views import ProfileView
from memoria.views import SettingsView

urlpatterns = [
    path("home/", HomePageView.as_view(), name="home"),
    path("galleries/", GalleriesView.as_view(), name="galleries"),
    path("albums/", AlbumsView.as_view(), name="albums"),
    path("people/", PeopleView.as_view(), name="people"),
    path("locations/", LocationsView.as_view(), name="locations"),
    path("dates/", DatesView.as_view(), name="dates"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("settings/", SettingsView.as_view(), name="settings"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html.jinja"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="logout.html.jinja"), name="logout"),
    path("admin/", admin.site.urls),
]
