from rest_framework import permissions
from typing import cast
from identity.models import User

class IsManager(permissions.BasePermission):
    """ Allows access only to users in the 'Manager' group. """
    def has_permission(self, request, view):
        user = cast(User, request.user) # make sure pylance know that user has group attribute
        return user.groups.filter(name="Manager").exists() 

class IsPaymentOwner(permissions.BasePermission):
    """ Keep customer lock their own data """
    def has_object_permission(self, request, view, obj):
        if obj.booking.user == request.user: # we check user on connected booking app
            return True
