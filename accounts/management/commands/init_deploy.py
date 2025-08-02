from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Run migrations and create a superuser for custom user model'

    def handle(self, *args, **kwargs):
        self.stdout.write("Running migrations...")
        call_command('migrate')

        User = get_user_model()
        username = 'admin'
        password = 'Welcome@123'
        email = 'admin@fitaccess.com'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(f"Custom superuser '{username}' created.")
        else:
            self.stdout.write(f"Superuser '{username}' already exists.")
