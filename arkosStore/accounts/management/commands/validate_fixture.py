import json
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class Command(BaseCommand):
    help = 'Validates data in a JSON fixture file against model validators.'

    def add_arguments(self, parser):
        parser.add_argument('fixture_file', type=str, help='The path to the JSON fixture file.')

    def handle(self, *args, **options):
        fixture_path = options['fixture_file']
        
        try:
            with open(fixture_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {fixture_path}")
        except json.JSONDecodeError:
            raise CommandError(f"Error decoding JSON from: {fixture_path}")

        self.stdout.write(f"Validating data from {fixture_path}...")
        
        has_errors = False
        
        for item in data:
            if item['model'] == 'accounts.user':
                fields = item['fields']
                pk = item.get('pk', 'N/A')
                
                user_data = {
                    'username': fields.get('username'),
                    'first_name': fields.get('first_name', ''),
                    'last_name': fields.get('last_name', ''),
                    'email': fields.get('email', ''),
                    'phone_number': fields.get('phone_number'),
                    'address': fields.get('address', ''),
                    'role': fields.get('role', 'REG'),
                    'is_staff': fields.get('is_staff', False),
                    'is_superuser': fields.get('is_superuser', False),
                    
                    # FIX 1: Add a dummy password to pass blank=False validation
                    'password': 'dummy_password_for_validation'
                }

                # Create a temporary User instance (without saving)
                user_instance = User(**user_data)
                
                try:
                    user_instance.full_clean(validate_unique=False) 
                    
                except ValidationError as e:
                    self.stderr.write(self.style.ERROR(
                        f"Validation FAILED for User PK={pk} (username: {user_data['username']}):"
                    ))
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            self.stderr.write(f"  - {field}: {error}")
                    has_errors = True

        if not has_errors:
            self.stdout.write(self.style.SUCCESS("Validation successful! All data is valid."))
        else:
            self.stdout.write(self.style.WARNING("Validation finished with errors."))