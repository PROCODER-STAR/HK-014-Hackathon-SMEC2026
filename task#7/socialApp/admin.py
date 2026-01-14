from django.contrib import admin
from .models import UserProfile, Follow, Post, Comment, Like

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'followers_count', 'following_count')
    search_fields = ('user__username',)

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__user__username', 'following__user__username')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('owner', 'created_at', 'likes_count', 'comments_count')
    search_fields = ('owner__user__username', 'message')
    date_hierarchy = 'created_at'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('made_by', 'post', 'created_at')
    search_fields = ('made_by__user__username', 'post__message', 'message')
    date_hierarchy = 'created_at'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('liked_by', 'post', 'created_at')
    search_fields = ('liked_by__user__username', 'post__message')
    date_hierarchy = 'created_at'

