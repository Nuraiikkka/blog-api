import logging

from celery import shared_task

logger = logging.getLogger('apps.users')


# Retries matter for email sending: SMTP servers can be temporarily unavailable,
# rate-limited, or slow to respond. Retry with backoff avoids hammering the mail
# server and gives transient failures time to recover.
@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_welcome_email(user_id: int) -> None:
    from django.contrib.auth import get_user_model
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils import translation

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning('send_welcome_email: user %s not found', user_id)
        return

    lang = user.preferred_language or 'en'
    with translation.override(lang):
        subject = render_to_string('emails/welcome/subject.txt', {'user': user}).strip()
        body = render_to_string('emails/welcome/body.txt', {'user': user})
        send_mail(subject, body, None, [user.email])
        logger.info('Welcome email sent to: %s', user.email)
