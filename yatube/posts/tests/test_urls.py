from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.other_user = User.objects.create_user(username='other')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user)

    def test_public_pages(self):
        """
        Проверка доступности страниц гостю
        и запроса несуществующей страницы.
        """
        url_context = {
            reverse('posts:index'): 200,
            reverse('posts:group_list', kwargs={
                'slug': f'{self.group.slug}'}): 200,
            reverse('posts:profile', kwargs={
                'username': f'{self.user.username}'}): 200,
            reverse('posts:post_detail', kwargs={
                'post_id': f'{self.post.id}'}): 200,
            reverse('posts:post_create'): 302,
            reverse('posts:post_edit', kwargs={
                'post_id': f'{self.post.id}'}): 302,
            '/unexisting_page/': 404,
        }
        for url, status in url_context.items():
            response = self.guest_client.get(url)
            with self.subTest(url=url):
                self.assertEqual(response.status_code, status)

    def test_create_page(self):
        """
        Проверка доступности страницы create/
        для авторизованного пользователя.
        """
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_edit_page(self):
        """Проверка доступности страницы редактирования поста для автора."""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_comment_page(self):
        """
        Проверка доступности комментирования авторизованному пользователю.
        """
        url = reverse(
            'posts:post_detail', kwargs={'post_id': f'{self.post.id}'}
        )
        response = self.authorized_client.get(url)
        expected = forms.fields.CharField
        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, expected)

    def test_url_uses_correct_template(self):
        """Проверка используемых шаблонов."""
        template_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': f'{self.group.slug}'}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': f'{self.user.username}'}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': f'{self.post.id}'}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': f'{self.post.id}'}): 'posts/create_post.html',
        }
        for address, template in template_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_follow_pages_availible(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        urls = [
            reverse('posts:profile_follow',
                kwargs={'username': self.other_user}),
            reverse('posts:profile_unfollow',
                kwargs={'username': self.other_user}),
        ]
        for url in urls:
            response = self.authorized_client.post(url)
            with self.subTest(url=url):
                self.assertEqual(response.status_code, 302)
                self.assertRedirects(
                    response, reverse(
                        'posts:profile',
                        kwargs={'username': self.other_user}
                    )
                )
