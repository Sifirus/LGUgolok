from django.urls import path
from approval import views

urlpatterns = [
    path('approval', views.approval_page, name='approval'),
    path('users/approver-lookup/', views.ApproverLookupAPIView.as_view(), name='approver_lookup_api'),
    path('api/approval/pending/', views.ApprovalPendingListAPIView.as_view(), name='api_approval_list'),
    path('api/approval/my-locked/', views.MyLockedApprovalsAPIView.as_view(), name='api_approval_my_locked'),
    path('api/approval/<int:pk>', views.ApprovalDetailAPIView.as_view(), name='api_approval_detail'),
    path('api/approval/<int:pk>/cancel', views.ApprovalDetailCancelAPIView.as_view(), name='api_approval_cancel'),
    path('api/approval/<int:pk>/decision', views.ApprovalDecisionAPIView.as_view(), name='api_approval_decision'),
]
