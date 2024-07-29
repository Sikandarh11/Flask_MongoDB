from flask import Flask
import firebase_admin
from firebase_admin import credentials, auth, storage
from google.cloud import storage as gcs
from google.oauth2 import service_account

app = Flask(__name__)
cred = credentials.Certificate("D:\\influential-kit-430506-m-45094-firebase-adminsdk-3gh5f-4781881dca.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'influential-kit-430506-m-45094.appspot.com'
})
gcs_credentials = service_account.Credentials.from_service_account_file("D:\\influential-kit-430506-m-45094-firebase-adminsdk-3gh5f-4781881dca.json")
gcs_client = gcs.Client(credentials=gcs_credentials)
bucket = storage.bucket()


