from rest_framework import permissions
from typing import cast
from identity.models import User

class IsManager(permissions.BasePermission):
    """ Allows access only to users in the 'Manager' group. """
    def has_permission(self, request, view):
        user = cast(User, request.user) # make sure pylance know that user has group attribute
        return user.groups.filter(name="Manager").exists() 

