import os

from settings.conf import config

ENV_ID = config('BLOG_ENV_ID', default='local')

if ENV_ID == 'prod':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.local')

from django.core.management import execute_from_command_line  # noqa: E402


def main() -> None:
    execute_from_command_line(os.sys.argv)


if __name__ == '__main__':
    main()