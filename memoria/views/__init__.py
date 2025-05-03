from memoria.views.albums import AlbumsView
from memoria.views.dates import DatesView
from memoria.views.folders import ImageFolderDetailView
from memoria.views.folders import ImageFolderListView
from memoria.views.home import HomePageView
from memoria.views.images import ImageDetailView
from memoria.views.images import ImageListView
from memoria.views.locations import LocationsView
from memoria.views.people import PeopleListView
from memoria.views.people import PersonDetailView
from memoria.views.people import PersonPhotosListView
from memoria.views.profile import ManageGroupsView
from memoria.views.profile import ProfileView
from memoria.views.profile import UpdateEmailView
from memoria.views.profile import UpdateProfileView
from memoria.views.settings import AddGroupView
from memoria.views.settings import AddUserView
from memoria.views.settings import AdminSettingsView
from memoria.views.settings import ManageUserGroupsView
from memoria.views.settings import RemoveGroupView
from memoria.views.settings import ToggleUserActiveView

__all__ = [
    "AddGroupView",
    "AddUserView",
    "AdminSettingsView",
    "AlbumsView",
    "DatesView",
    "HomePageView",
    "ImageDetailView",
    "ImageFolderDetailView",
    "ImageFolderListView",
    "ImageListView",
    "LocationsView",
    "ManageGroupsView",
    "ManageUserGroupsView",
    "PeopleListView",
    "PersonDetailView",
    "PersonPhotosListView",
    "ProfileView",
    "RemoveGroupView",
    "ToggleUserActiveView",
    "UpdateEmailView",
    "UpdateProfileView",
]
