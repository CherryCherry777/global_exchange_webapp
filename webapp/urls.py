from django.urls import path
from . import views
from .views import CustomLoginView

#aqui van las url para el programa, si no estaan aqui no seran accesibles
urlpatterns = [
    path("landing/", views.landing_page, name="landing"),
    path("register/", views.register, name="register"),
    path("verify/<uidb64>/<token>/", views.verify_email, name="verify-email"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path('logout/', views.custom_logout, name='logout'),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("admin_dashboard/", views.admin_dash, name="admin_dashboard"),
    path("employee_dashboard/", views.employee_dash, name="employee_dashboard"),
    path("manage_user_roles/", views.manage_user_roles, name="manage_user_roles"),
    path('', views.public_home, name='public_home'),
    path('manage_user_roles/<int:user_id>/<str:role>/', views.manage_user_roles, name='assign_role'),
    path('remove_role/<int:user_id>/<str:role>/', views.remove_role, name='remove_role'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user-create'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('manage_user_roles/', views.manage_user_roles, name='manage_user_roles'),
    path('add_role/<int:user_id>/', views.add_role, name='add_role'),
    path('remove_role/<int:user_id>/<str:role>/', views.remove_role, name='remove_role'),

]