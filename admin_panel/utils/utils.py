from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail


def send_new_user_email(email, temp_password):
    subject = render_to_string(
        'admin_panel/new_user_email_subject.txt',
        context={'site_name': 'ЛГУголок'}
    )
    message = render_to_string(
        'admin_panel/new_user_email.html',
        context={'email': email, 'temp_password': temp_password}
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
