from rest_framework import permissions


class OwnerAuthenticated(permissions.IsAuthenticated):
	def has_object_permission(self, request, view, obj):
		return self.has_permission(request, view) and obj.user == request.user


class IsRestaurantOwner(permissions.IsAuthenticated):
	def has_permission(self, request, view):
		return super().has_permission(request, view) and request.user.role == 'restaurant'
