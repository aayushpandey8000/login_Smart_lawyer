import streamlit as st
import firebase_admin
from firebase_admin import auth, credentials, initialize_app, exceptions
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2
import base64

# Background image styling
background_image = """
<style>
[data-testid="stAppViewContainer"] > .main {
    background-image: url("https://i.ibb.co/rwQBRdJ/magicpattern-mesh-gradient-1715094470100.png");
    background-size: 100vw 100vh;
    background-position: center;
    background-repeat: no-repeat;
}
</style>
"""
st.markdown(background_image, unsafe_allow_html=True)

# Firebase configuration from secrets
firebase_config = {
    "type": st.secrets["firebase"]["type"],
    "project_id": st.secrets["firebase"]["project_id"],
    "private_key_id": st.secrets["firebase"]["private_key_id"],
    "private_key": st.secrets["firebase"]["private_key"],
    "client_email": st.secrets["firebase"]["client_email"],
    "client_id": st.secrets["firebase"]["client_id"],
    "auth_uri": st.secrets["firebase"]["auth_uri"],
    "token_uri": st.secrets["firebase"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
}

# Initialize Firebase app
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate(firebase_config)
    initialize_app(cred)

# Google OAuth2 credentials from secrets
client_id = st.secrets["google_oauth"]["client_id"]
client_secret = st.secrets["google_oauth"]["client_secret"]
redirect_url = st.secrets["google_oauth"]["redirect_url"]

# Initialize Google OAuth2 client
client = GoogleOAuth2(client_id=client_id, client_secret=client_secret)

# Initialize session state email
if 'email' not in st.session_state:
    st.session_state.email = ''

# Async functions to handle OAuth2
async def get_access_token(client: GoogleOAuth2, redirect_url: str, code: str):
    return await client.get_access_token(code, redirect_url)

async def get_email(client: GoogleOAuth2, token: str):
    user_id, user_email = await client.get_id_email(token)
    return user_id, user_email

def get_logged_in_user_email():
    try:
        query_params = st.query_params()
        code = query_params.get('code')
        if code:
            token = asyncio.run(get_access_token(client, redirect_url, code[0]))
            user_id, user_email = asyncio.run(get_email(client, token['access_token']))
            st.session_state.email = user_email
            return user_email
    except Exception as e:
        st.error(f"An error occurred: {e}")
    return None

# Display login button or user email
user_email = get_logged_in_user_email()
if user_email:
    st.write(f"Welcome, {user_email}!")
else:
    auth_url = client.get_authorization_url(redirect_url, scope=["openid", "email", "profile"])
    st.markdown(f'[Login with Google]({auth_url})')

# Add your Streamlit app content here
st.title('My Streamlit App')
st.write('Your app content goes here.')
