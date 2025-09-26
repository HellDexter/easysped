import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.count() == 0:
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            if not username or not password:
                self.stdout.write(self.style.ERROR(
                    'DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD must be set in environment variables.'
                ))
                return

            self.stdout.write(f'Creating account for {username}')
            admin = User.objects.create_superuser(email=email, username=username, password=password)
            admin.save()
        else:
            self.stdout.write('Admin account can only be initialized if no Users exist')
