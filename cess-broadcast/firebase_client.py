import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

load_dotenv()


def get_secret(nome, default=None):
    try:
        import streamlit as st
        if nome in st.secrets:
            return st.secrets[nome]
    except Exception:
        pass

    return os.getenv(nome, default)


def get_firestore_client():
    if not firebase_admin._apps:
        private_key = get_secret("FIREBASE_PRIVATE_KEY")

        if not private_key:
            raise ValueError("FIREBASE_PRIVATE_KEY não foi encontrada.")

        cred_dict = {
            "type": get_secret("FIREBASE_TYPE"),
            "project_id": get_secret("FIREBASE_PROJECT_ID"),
            "private_key_id": get_secret("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": private_key.replace("\\n", "\n"),
            "client_email": get_secret("FIREBASE_CLIENT_EMAIL"),
            "client_id": get_secret("FIREBASE_CLIENT_ID"),
            "auth_uri": get_secret("FIREBASE_AUTH_URI"),
            "token_uri": get_secret("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": get_secret("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": get_secret("FIREBASE_CLIENT_CERT_URL"),
            "universe_domain": get_secret("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com"),
        }

        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)

    return firestore.client()


def buscar_aberturas_por_semana(semana):
    db = get_firestore_client()

    docs = (
        db.collection("aberturas")
        .where(filter=FieldFilter("semana", "==", semana))
        .stream()
    )

    return [doc.to_dict() for doc in docs]