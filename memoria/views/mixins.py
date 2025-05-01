from django.contrib.auth.mixins import UserPassesTestMixin


class UserIsActiveStaffOrSuperuserTestMixin(UserPassesTestMixin):
    """
    A user must be an active staff or superuser to pass this test
    """

    def test_func(self) -> bool:
        """
        Only allow active staff users to access this view.
        """
        return self.request.user.is_active and (self.request.user.is_staff or self.request.is_superuser)
