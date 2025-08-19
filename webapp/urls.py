from django.urls import path
from . import views

#aqui van las url para el programa, si no estaan aqui no seran accesibles
urlpatterns = [
    path("register/", views.register, name="register"),
    path("verify/<uidb64>/<token>/", views.verify_email, name="verify-email"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
]