from rest_framework import permissions
from typing import cast
from identity.models import User

class IsManagerOrReadonly(permissions.BasePermission):
    """
    - Allows ANYONE to see the data (GET).
    - Only allows MANAGERS to change the data (POST, PATCH, DELETE).
    """
    def has_permission(self, request, view):
        user = cast(User, request.user)

        if request.method in permissions.SAFE_METHODS: # if the request is a "Safe" method (GET, HEAD, OPTIONS)
            return True
        return (# Otherwise if the request is a "Write" method
            request.user.is_authenticated and
            user.groups.filter(name="Manager").exists()
        ) 


class IsManager(permissions.BasePermission):
    """ Allows access only to users in the 'Manager' group. """
    def has_permission(self, request, view):
        user = cast(User, request.user) # make sure pylance know that user has group attribute
        return user.groups.filter(name="Manager").exists() 


class IsWorker(permissions.BasePermission):
    """ Allows access only to users in the 'Worker' group. """
    def has_permission(self, request, view):
        user = cast(User, request.user)
        return user.groups.filter(name="Worker").exists() 
