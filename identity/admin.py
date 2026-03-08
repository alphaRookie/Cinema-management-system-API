from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .services import UserService

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # 1. The list view (you already have this)
    list_display = ("email", "username", "is_staff", "is_cinema_vip")

    # 3. Organize the edit/creation page into sections
    # now after creating a spesific user, we allow to make/add/assign some changes
    fieldsets = (
        (None, {"fields": ("username", "password")}), # No blue horizontal line
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number")}),
        ("Business Status", {"fields": ("is_cinema_vip",)}),
        ("Permissions", {
            "classes": ("collapse",), # allow to collapse
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # 2. Use this for the "Add User" form specifically
    # these are 5 fields needed to be added when creating a user
    add_fieldsets = BaseUserAdmin.add_fieldsets + ( # 2 more refer to fieldset
        (None, {"fields": ("email", "phone_number", "is_cinema_vip")}),
    )

    search_fields = ("email", "username")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined")


    # Object-Level-Permission (Prevent admin to access superuser record)
    # 1. Dont show superuser in the list (manager cant see)
    def get_queryset(self, request):
        qs = super().get_queryset(request) # same as `User.objects.all()`, but this remember all rules
        if not request.user.is_superuser: #type:ignore
            return qs.filter(is_superuser=False) # Hide all superusers from the list of admins (they only see normal user)
        return qs # if its indeed superuser, show all
        
    # 2. this is second layer if they somehow they can find via URL
    def has_change_permission(self, request, obj=None):
        # If the Target (obj) exist which is a superuser, but the Actor (request.user) is not
        UserService.can_manage_target(request.user, obj) #check the rule book #type:ignore

        # when we use: "Check my special rule first. If my rule doesn't apply, go back and do what you usually do(refer to parent)"
        return super().has_change_permission(request, obj)


    # blocking some fields
    def get_readonly_fields(self, request, obj=None):
        # Get the existing readonly fields
        readonly = list(super().get_readonly_fields(request, obj)) # why list? so we can extend ; bcoz tuple is non-editable 
        
        extra_locks = UserService.can_access_field(request.user, obj) # check the rule book #type:ignore

        readonly.extend(extra_locks) # now we extend (still as list)
        return tuple(readonly) # now we seal the book again (by turn back tuple)

