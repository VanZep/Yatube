import shutil
import tempfile

from django import forms
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, User, Comment
from ..constants import NUMBER_OF_POSTS, NUMBER_OF_POSTS_TEST


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    """Тестирует view-функции."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Автор поста')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='gif.gif',
            content=cls.gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(ViewsTests.user)

    def checking_post_attributes(self, post):
        """Проверка атрибутов поста."""
        self.assertEqual(post.text, ViewsTests.post.text)
        self.assertEqual(post.author, ViewsTests.post.author)
        self.assertEqual(post.group, ViewsTests.post.group)
        self.assertEqual(post.pk, ViewsTests.post.pk)
        self.assertEqual(post.image, ViewsTests.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        kwargs_post_id = {'post_id': ViewsTests.post.pk}
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={
                    'slug': ViewsTests.group.slug
                }
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={
                    'username': ViewsTests.user.username
                }
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs=kwargs_post_id
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs=kwargs_post_id
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        self.checking_post_attributes(response.context['page_obj'][0])

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(
            reverse(
                'posts:group_list', kwargs={'slug': ViewsTests.group.slug}
            )
        )
        self.assertEqual(
            response.context.get('group').title, ViewsTests.group.title
        )
        self.assertEqual(
            response.context.get('group').slug, ViewsTests.group.slug
        )
        self.assertEqual(
            response.context.get('group').description, (
                ViewsTests.group.description
            )
        )
        self.checking_post_attributes(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse(
                'posts:profile', kwargs={'username': ViewsTests.user.username}
            )
        )
        self.assertEqual(
            response.context.get('author'), ViewsTests.post.author
        )
        self.checking_post_attributes(response.context['page_obj'][0])

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': ViewsTests.post.pk}
            )
        )
        comment = response.context['comments'][0]
        form_fields = {
            'text': forms.fields.CharField
        }
        self.assertEqual(
            response.context.get('post').text, ViewsTests.post.text
        )
        self.assertEqual(
            response.context.get('post').author, ViewsTests.post.author
        )
        self.assertEqual(
            response.context.get('post').group, ViewsTests.post.group
        )
        self.assertEqual(
            response.context.get('post').pk, ViewsTests.post.pk
        )
        self.assertEqual(
            response.context.get('post').image, ViewsTests.post.image
        )
        self.assertEqual(comment.text, ViewsTests.comment.text)
        self.assertEqual(comment.post, ViewsTests.comment.post)
        self.assertEqual(comment.author, ViewsTests.comment.author)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.auth_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.auth_client.get(
            reverse(
                'posts:post_edit', kwargs={'post_id': ViewsTests.post.pk}
            )
        )
        form_fields = {
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))

    def test_new_post_first_position_of_index_page(self):
        """Новый пост занимает первую позицию на странице index."""
        new_post = Post.objects.create(
            author=ViewsTests.user,
            group=ViewsTests.group,
            text=ViewsTests.post.text
        )
        response = self.client.get(reverse('posts:index'))
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post, new_post)

    def test_new_post_first_position_of_group_list_page(self):
        """Новый пост занимает первую позицию на странице group_list."""
        new_post = Post.objects.create(
            author=ViewsTests.user,
            group=ViewsTests.group,
            text=ViewsTests.post.text
        )
        response = self.client.get(
            reverse(
                'posts:group_list', kwargs={'slug': ViewsTests.group.slug}
            )
        )
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post, new_post)

    def test_new_post_first_position_of_profile_page(self):
        """Новый пост занимает первую позицию на странице profile."""
        new_post = Post.objects.create(
            author=ViewsTests.user,
            group=ViewsTests.group,
            text=ViewsTests.post.text
        )
        response = self.client.get(
            reverse(
                'posts:profile', kwargs={'username': ViewsTests.user.username}
            )
        )
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post, new_post)

    def test_new_post_not_in_wrong_group(self):
        """Новый пост не попал в контекст чужой группы."""
        wrong_group = Group.objects.create(
            title='ошибочная группа',
            slug='wrong-slug',
            description='ошибочное описание группы'
        )
        new_post = Post.objects.create(
            author=ViewsTests.user,
            group=ViewsTests.group,
            text=ViewsTests.post.text
        )
        response = self.client.get(
            reverse(
                'posts:group_list', kwargs={'slug': wrong_group.slug}
            )
        )
        wrong_group_objects = response.context['page_obj']
        self.assertNotIn(new_post, wrong_group_objects)

    def test_cache_index_page(self):
        """Проверка кеширования страницы index."""
        response = self.auth_client.get(reverse('posts:index'))
        page_content = response.content
        Post.objects.first().delete()
        response = self.auth_client.get(reverse('posts:index'))
        cached_page_content = response.content
        cache.clear()
        response = self.auth_client.get(reverse('posts:index'))
        self.assertEqual(page_content, cached_page_content)
        self.assertNotEqual(page_content, response.content)
        self.assertNotEqual(cached_page_content, response.content)


class PaginatorViewsTests(TestCase):
    """Тестирует Paginator для view-функций."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.bulk_create([
            Post(
                author=cls.user,
                group=cls.group,
                text='Тестовый текст поста'
            ) for _ in range(NUMBER_OF_POSTS_TEST)
        ])

    def test_index_first_page_pagination(self):
        """Проверка пагинации первой страницы index."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POSTS)

    def test_index_second_page_pagination(self):
        """Проверка пагинации второй страницы index."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), (
            NUMBER_OF_POSTS_TEST - NUMBER_OF_POSTS))

    def test_group_list_first_page_pagination(self):
        """Проверка пагинации первой страницы group_list."""
        response = self.client.get(
            reverse(
                'posts:group_list', kwargs={
                    'slug': PaginatorViewsTests.group.slug
                }
            )
        )
        self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POSTS)

    def test_group_list_second_page_pagination(self):
        """Проверка пагинации второй страницы group_list."""
        response = self.client.get(
            reverse(
                'posts:group_list', kwargs={
                    'slug': PaginatorViewsTests.group.slug
                }
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), (
            NUMBER_OF_POSTS_TEST - NUMBER_OF_POSTS))

    def test_profile_first_page_pagination(self):
        """Проверка пагинации первой страницы profile."""
        response = self.client.get(
            reverse(
                'posts:profile', kwargs={
                    'username': PaginatorViewsTests.user.username
                }
            )
        )
        self.assertEqual(len(response.context['page_obj']), NUMBER_OF_POSTS)

    def test_profile_second_page_pagination(self):
        """Проверка пагинации второй страницы profile."""
        response = self.client.get(
            reverse(
                'posts:profile', kwargs={
                    'username': PaginatorViewsTests.user.username
                }
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), (
            NUMBER_OF_POSTS_TEST - NUMBER_OF_POSTS))
