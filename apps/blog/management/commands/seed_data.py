import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.blog.models import Category, Comment, Post, Tag
from apps.blog.constants import PostStatus

logger = logging.getLogger('apps.blog')

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **options) -> None:
        self.stdout.write('Seeding database...')

        users = self._create_users()
        categories = self._create_categories()
        tags = self._create_tags()
        posts = self._create_posts(users, categories, tags)
        self._create_comments(posts, users)

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

    def _create_users(self) -> list:
        users = []
        user_data = [
            {'email': 'alice@example.com', 'first_name': 'Alice', 'last_name': 'Smith', 'preferred_language': 'en'},
            {'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Jones', 'preferred_language': 'ru'},
            {'email': 'carol@example.com', 'first_name': 'Carol', 'last_name': 'Brown', 'preferred_language': 'kk'},
        ]
        for data in user_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'preferred_language': data['preferred_language'],
                },
            )
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
        self.stdout.write(f'  Created {len(users)} users')
        return users

    def _create_categories(self) -> list:
        categories = []
        cat_data = [
            {'slug': 'technology', 'en': 'Technology', 'ru': 'Технологии', 'kk': 'Технология'},
            {'slug': 'science', 'en': 'Science', 'ru': 'Наука', 'kk': 'Ғылым'},
            {'slug': 'culture', 'en': 'Culture', 'ru': 'Культура', 'kk': 'Мәдениет'},
        ]
        for data in cat_data:
            cat, created = Category.objects.get_or_create(slug=data['slug'])
            if created:
                cat.set_current_language('en')
                cat.name = data['en']
                cat.save()
                cat.set_current_language('ru')
                cat.name = data['ru']
                cat.save()
                cat.set_current_language('kk')
                cat.name = data['kk']
                cat.save()
            categories.append(cat)
        self.stdout.write(f'  Created {len(categories)} categories')
        return categories

    def _create_tags(self) -> list:
        tags = []
        tag_names = ['python', 'django', 'rest-api', 'machine-learning', 'web']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name, defaults={'slug': slugify(name)})
            tags.append(tag)
        self.stdout.write(f'  Created {len(tags)} tags')
        return tags

    def _create_posts(self, users: list, categories: list, tags: list) -> list:
        posts = []
        post_data = [
            {'title': 'Getting Started with Django', 'status': PostStatus.PUBLISHED, 'user_idx': 0, 'cat_idx': 0},
            {'title': 'Advanced Python Tips', 'status': PostStatus.PUBLISHED, 'user_idx': 0, 'cat_idx': 0},
            {'title': 'REST API Best Practices', 'status': PostStatus.PUBLISHED, 'user_idx': 1, 'cat_idx': 0},
            {'title': 'Machine Learning Basics', 'status': PostStatus.PUBLISHED, 'user_idx': 1, 'cat_idx': 1},
            {'title': 'Deep Dive into Neural Networks', 'status': PostStatus.DRAFT, 'user_idx': 2, 'cat_idx': 1},
            {'title': 'Kazakh Culture Overview', 'status': PostStatus.PUBLISHED, 'user_idx': 2, 'cat_idx': 2},
            {'title': 'Russian Literature Classics', 'status': PostStatus.PUBLISHED, 'user_idx': 0, 'cat_idx': 2},
            {'title': 'Web Development Trends 2024', 'status': PostStatus.DRAFT, 'user_idx': 1, 'cat_idx': 0},
            {'title': 'Database Optimization', 'status': PostStatus.PUBLISHED, 'user_idx': 2, 'cat_idx': 0},
            {'title': 'Cloud Computing Overview', 'status': PostStatus.PUBLISHED, 'user_idx': 0, 'cat_idx': 1},
            {'title': 'Open Source Contributions', 'status': PostStatus.PUBLISHED, 'user_idx': 1, 'cat_idx': 2},
            {'title': 'Data Structures in Python', 'status': PostStatus.PUBLISHED, 'user_idx': 2, 'cat_idx': 0},
        ]
        for data in post_data:
            slug = slugify(data['title'])
            post, created = Post.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': data['title'],
                    'body': f"This is the content of '{data['title']}'. " * 10,
                    'author': users[data['user_idx']],
                    'category': categories[data['cat_idx']],
                    'status': data['status'],
                },
            )
            if created:
                post.tags.set(tags[:3])
            posts.append(post)
        self.stdout.write(f'  Created {len(posts)} posts')
        return posts

    def _create_comments(self, posts: list, users: list) -> None:
        count = 0
        for post in posts[:8]:
            for user in users:
                if not Comment.objects.filter(post=post, author=user).exists():
                    Comment.objects.create(
                        post=post,
                        author=user,
                        body=f"Great post! This is a comment from {user.first_name}.",
                    )
                    count += 1
        self.stdout.write(f'  Created {count} comments')