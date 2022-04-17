import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.other_user = User.objects.create_user(username='other')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
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
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0.username, 'auth')
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_group_0.title, 'Тестовая группа')
        self.assertEqual(post_image_0, self.post.image)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.guest_client.
                    get(reverse('posts:group_list',
                        kwargs={'slug': f'{self.group.slug}'})))
        first_object = response.context['page_obj'][0]
        post_image_0 = first_object.image
        self.assertEqual(response.context.get(
            'group').title, 'Тестовая группа')
        self.assertEqual(response.context.get(
            'group').slug, 'test_slug')
        self.assertEqual(response.context.get(
            'group').description, 'Тестовое описание')
        self.assertEqual(post_image_0, self.post.image)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
                    )
        response1 = (self.authorized_client.get(reverse('posts:profile',
                     kwargs={'username': PostPagesTests.user.username})))
        first_object = response1.context['page_obj'][0]
        post_image_0 = first_object.image
        self.assertEqual(response.context.get('user').username, 'HasNoName')
        self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.guest_client.
                    get(reverse('posts:post_detail',
                        kwargs={'post_id': f'{self.post.id}'})))
        response1 = (self.authorized_client.get(reverse('posts:profile',
                     kwargs={'username': PostPagesTests.user.username})))
        first_object = response1.context['page_obj'][0]
        post_image_0 = first_object.image
        self.assertEqual(response.context.get('post').author.username, 'auth')
        self.assertEqual(response.context.get('post').text, 'Тестовый пост')
        self.assertEqual(response.context.get(
            'post').group.title, 'Тестовая группа')
        self.assertEqual(post_image_0, self.post.image)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_edit_show_correct_context(self):
        """
        Шаблон create_post для редактирования
        сформирован с правильным контекстом.
        """
        response = self.author_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': f'{self.post.id}'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_showed_on_correct_pages(self):
        """
        Проверка, что если при создании поста указать группу,
        то этот пост появляется на главной странице сайта,
        на странице выбранной группы, в профайле пользователя.
        Проверка, что этот пост не попал в группу,
        для которой не был предназначен.
        """
        page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': f'{PostPagesTests.group.slug}'}),
            reverse('posts:profile', kwargs={
                'username': f'{PostPagesTests.user.username}'})
        ]
        for page_name in page_names:
            with self.subTest(page_name=page_name):
                response = self.authorized_client.get(page_name)
                object = response.context.get('page_obj').object_list
                self.assertIn(self.post, object)

    def test_comment_showed_on_post_id_page(self):
        """
        Проверка, что после успешной отправки
        комментарий появляется на странице поста."""
        comments_count = Comment.objects.count()
        url = reverse(
            'posts:add_comment', kwargs={'post_id': f'{self.post.id}'}
        )
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            url,
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый коммент'
            ).exists()
        )
        self.assertEqual(response.status_code, 200)

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы."""
        new_post = Post.objects.create(
            author=self.user,
            text='Текст не попадет в кэш',
            group=self.group,
        )
        response = self.guest_client.get(reverse('posts:index'))
        object1 = response.content
        new_post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        object2 = response.content
        self.assertEqual(object1, object2)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        object3 = response.content
        self.assertNotEqual(object1, object3)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Page_user')
        cls.other_user = User.objects.create_user(username='other')
        cls.group = Group.objects.create(
            title='Тестовая группа1',
            slug='test_slug1',
            description='Тестовое описание группы1',
        )
        cls.posts = []
        for i in range(0, 11):
            cls.posts.append(Post.objects.create(
                text=f'Тестовый текст поста{i}',
                author=cls.user,
                group=cls.group,
            ))

    def setUp(self):
        self.guest_client = Client()
        self.text = 'что-нибудь'
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """
        Проверка количества постов на 1 странице
        index, group_list, profile.
        """
        page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': f'{self.group.slug}'}),
            reverse('posts:profile', kwargs={
                'username': f'{self.user.username}'})
        ]
        for page_name in page_names:
            with self.subTest(page_name=page_name):
                response = self.guest_client.get(page_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_one_record(self):
        """
        Проверка количества постов на 2 странице
        index, group_list, profile.
        """
        page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': f'{self.group.slug}'}),
            reverse('posts:profile', kwargs={
                'username': f'{self.user.username}'})
        ]
        for page_name in page_names:
            with self.subTest(page_name=page_name):
                response = self.guest_client.get(
                    reverse('posts:index') + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 1)

    def test_new_post_in_feed(self):
        """
        Новая запись пользователя появляется в ленте подписавшихся
        и не появляется в ленте тех, кто не подписан.
        """
        new_author = User.objects.create(username='new_author')
        Follow.objects.create(user=self.user, author=new_author)
        post = Post.objects.create(author=new_author, text=self.text)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        object = response.context.get('page_obj').object_list
        self.assertIn(post, object)
        following = self.user.follower.filter(author=new_author)
        following.delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        object = response.context.get('page_obj').object_list
        self.assertNotIn(post, object)
