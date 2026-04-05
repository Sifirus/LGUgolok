from rest_framework.permissions import BasePermission

class IsApprover(BasePermission):

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.role == 'approver' or request.user.role == 'operator' #TODO убрать на релизе
        else:
            return False
