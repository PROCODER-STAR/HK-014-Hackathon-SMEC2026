from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.user.username

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return self.following.count()


class Follow(models.Model):
    follower = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="following"
    )
    following = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_follow"
            )
        ]

    def clean(self):
        if self.follower == self.following:
            raise ValidationError("Users cannot follow themselves")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.follower} follows {self.following}"


class Post(models.Model):
    owner = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.owner} - {self.created_at}"

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    made_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.made_by} on {self.post}"


class Like(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    liked_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'liked_by')
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'liked_by'],
                name='unique_like'
            )
        ]

    def __str__(self):
        return f"{self.liked_by} likes {self.post}"
