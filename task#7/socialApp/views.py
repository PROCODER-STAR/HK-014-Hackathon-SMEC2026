from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import UserProfile, Post, Comment, Like, Follow


# Create your views here.
def index(request):
    posts = Post.objects.all()
    return render(request, 'socialApp/index.html', {'posts': posts})


class UserLoginView(LoginView):
    template_name = 'socialApp/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('index')


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('login')


class UserSignupView(CreateView):
    model = User
    template_name = 'socialApp/signup.html'
    fields = ['username', 'email', 'password']
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        messages.success(self.request, 'Account created successfully! Please log in.')
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sign Up'
        return context


@login_required(login_url='login')
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    posts = Post.objects.filter(owner=user_profile)
    return render(request, 'socialApp/profile.html', {'user_profile': user_profile, 'posts': posts})


@login_required(login_url='login')
def create_post(request):
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            Post.objects.create(owner=user_profile, message=message)
            messages.success(request, 'Post created successfully!')
        return redirect('index')
    return render(request, 'socialApp/create_post.html')


@login_required(login_url='login')
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.owner.user != request.user:
        messages.error(request, 'You can only delete your own posts!')
        return redirect('index')
    post.delete()
    messages.success(request, 'Post deleted successfully!')
    return redirect('index')


@login_required(login_url='login')
def create_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        message = request.POST.get('message', '').strip()
        if message:
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            Comment.objects.create(post=post, made_by=user_profile, message=message)
            messages.success(request, 'Comment added!')
        return redirect('index')
    return redirect('index')


@login_required(login_url='login')
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post_id = comment.post.id
    if comment.made_by.user != request.user:
        messages.error(request, 'You can only delete your own comments!')
        return redirect('index')
    comment.delete()
    messages.success(request, 'Comment deleted!')
    return redirect('index')


@login_required(login_url='login')
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    like = Like.objects.filter(post=post, liked_by=user_profile).first()
    
    if like:
        like.delete()
        liked = False
    else:
        Like.objects.create(post=post, liked_by=user_profile)
        liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': post.likes_count})
    return redirect('index')


@login_required(login_url='login')
def follow_user(request, profile_id):
    target_profile = get_object_or_404(UserProfile, id=profile_id)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if user_profile == target_profile:
        messages.error(request, 'You cannot follow yourself!')
        return redirect('index')
    
    follow = Follow.objects.filter(follower=user_profile, following=target_profile).first()
    if not follow:
        Follow.objects.create(follower=user_profile, following=target_profile)
        messages.success(request, f'You followed {target_profile.user.username}!')
    
    return redirect('index')


@login_required(login_url='login')
def unfollow_user(request, profile_id):
    target_profile = get_object_or_404(UserProfile, id=profile_id)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    follow = Follow.objects.filter(follower=user_profile, following=target_profile).first()
    if follow:
        follow.delete()
        messages.success(request, f'You unfollowed {target_profile.user.username}!')
    
    return redirect('index')
