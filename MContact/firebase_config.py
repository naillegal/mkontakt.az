import firebase_admin
from firebase_admin import credentials

try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()
