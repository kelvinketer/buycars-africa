from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Sends a test email to verify credentials'

    def handle(self, *args, **kwargs):
        self.stdout.write("Attempting to send test email...")

        try:
            # We use the settings from settings.py, which grab the secure env vars
            send_mail(
                subject='Test from Render Server',
                message='If you are reading this, your email configuration on Render is 100% correct!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_HOST_USER], # Sends to yourself
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('✅ Email sent successfully! Check your inbox.'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to send email: {e}'))