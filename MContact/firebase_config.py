import os
from django.conf import settings
import firebase_admin
from firebase_admin import credentials

cred_path = os.path.join(settings.BASE_DIR, 'mkontakt-firebase.json')

cred = credentials.Certificate(cred_path)

try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)
