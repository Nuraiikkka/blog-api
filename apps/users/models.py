import logging

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.constants import LANGUAGE_CHOICES, LANGUAGE_EN

logger = logging.getLogger('apps.users')


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str, **extra_fields) -> 'User':
        if not email:
            raise ValueError(_('Email is required'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        logger.info('User created: %s', email)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields) -> 'User':
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default=LANGUAGE_EN,
    )
    timezone = models.CharField(
        _('timezone'),
        max_length=100,
        default='UTC',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'
