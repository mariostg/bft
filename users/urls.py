from django.urls import path
from users import views

urlpatterns = [
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("profile/", views.user_profile, name="profile"),
    path("register/", views.register_new_user, name="register"),
    path("user-table/", views.user_page, name="user-table"),
    path("user-add/", views.user_add, name="user-add"),
    path("user-update/<int:pk>", views.user_update, name="user-update"),
    path("user-delete/<int:pk>", views.user_delete, name="user-delete"),
    path("user-password-reset/<int:pk>", views.user_password_reset, name="user-password-reset"),
]
