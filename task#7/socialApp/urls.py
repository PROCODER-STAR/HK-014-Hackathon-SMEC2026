from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('signup/', views.UserSignupView.as_view(), name='signup'),
    path('profile/', views.profile, name='profile'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('comment/<int:post_id>/create/', views.create_comment, name='create_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('follow/<int:profile_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:profile_id>/', views.unfollow_user, name='unfollow_user'),
]
