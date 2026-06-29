from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Seed the database with a default Admin user'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword',
                role=User.RoleChoices.ADMIN,
                first_name='Super',
                last_name='Admin',
                departement='Direction',
                telephone='0000000000'
            )
            self.stdout.write(self.style.SUCCESS('Successfully created default Admin user (username: admin, password: adminpassword)'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists.'))
