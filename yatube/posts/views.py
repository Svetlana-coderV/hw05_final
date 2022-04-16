from datetime import datetime
from typing import Dict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User


def index(request: HttpRequest) -> HttpResponse:
    """Функция-обработчик для главной страницы. """
    posts: str = Post.objects.all()
    paginator = Paginator(posts, settings.NUMB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context: Dict[str, str] = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request: HttpRequest, slug: str) -> HttpRequest:
    """Функция-обработчик для страницы с постами."""
    group: str = get_object_or_404(Group, slug=slug)
    posts: str = Post.objects.filter(group=group).all()
    paginator = Paginator(posts, settings.NUMB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context: Dict[str, str] = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Страница профайла пользователя, содержит инфо об авторе и посты."""
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    posts_count = author.posts.count()
    paginator = Paginator(posts, settings.NUMB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    user = request.user
    following = (
        user.is_authenticated and user.follower.filter(author=author).exists()
    )
    context = {
        'page_obj': page_obj,
        'author': author,
        'posts_count': posts_count,
        'user': user,
        'following': following,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Подробная информация об отдельном посте."""
    post = get_object_or_404(Post, pk=post_id)
    group = post.group
    author = post.author
    posts_count = author.posts.count()
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'group': group,
        'posts_count': posts_count,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    """Создание нового поста."""
    if request.method != 'POST':
        form = PostForm(
            files=request.FILES or None
        )
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm(
        request.POST,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.pub_date = datetime.now()
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request: HttpRequest, post_id) -> HttpResponse:
    """Редактирование поста."""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if not form.is_valid():
        context = {
            'form': form,
            'is_edit': True
        }
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request: HttpRequest, post_id) -> HttpResponse:
    """Добавление комментария."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request: HttpRequest) -> HttpResponse:
    """
    Функция страницы постов авторов,
    на которых подписан текущий пользователь.
    """
    user = request.user
    authors = user.follower.values_list('author', flat=True)
    posts = Post.objects.filter(author__id__in=authors)
    paginator = Paginator(posts, settings.NUMB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context: Dict[str, str] = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request: HttpRequest, username) -> HttpResponse:
    """Функция страницы подписки на авторов."""
    user = request.user
    author = User.objects.get(username=username)
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request: HttpRequest, username) -> HttpResponse:
    """Функция страницы отписки от авторов."""
    user = request.user
    author = User.objects.get(username=username)
    following = user.follower.filter(author=author)
    following.delete()
    return redirect('posts:profile', username)
