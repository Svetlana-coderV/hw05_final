from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_model_post_has_correct_object_name(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = self.post
        string = post.text
        self.assertEqual(string, str(post))

    def test_model_group_has_correct_object_name(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = self.group
        string = group.title
        self.assertEqual(string, str(group))
