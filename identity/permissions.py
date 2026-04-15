from rest_framework import permissions
from typing import cast
from identity.models import User

class IsOwner(permissions.BasePermission):
    """ Checks if the person asking is the owner of the specific Account """
    def has_object_permission(self, request, view, obj): # ORDER MATTERS HERE, `obj` must be the last
        if obj == request.user: # if the obj(our profile) == person who logged in
            return True
        
class IsManager(permissions.BasePermission):
    """ Allows access only to users in the 'Manager' group. """
    def has_permission(self, request, view):
        user = cast(User, request.user) # make sure pylance know that user has group attribute
        return user.groups.filter(name="Manager").exists() 
