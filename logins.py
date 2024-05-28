import streamlit as st
import firebase_admin
from firebase_admin import auth, exceptions, credentials, initialize_app
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2
import json
import base64

# Function to get base64 representation of a binary file
@st.cache_data()
def get_base64_of_bin_file(bin_file, mutable=True):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Function to set background image
def set_background(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    .stApp {{
    background-image: url("data:image/jpeg;base64,{bin_str}");
    background-size: cover;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Set background image
set_background("D:/py_llm/law/magicpattern-mesh-gradient-1715052764545.png")

# Initialize Firebase app with Streamlit secrets
firebase_key = json.loads(st.secrets["firebase_key"])
cred = credentials.Certificate(firebase_key)
try:
    firebase_admin.get_app()
except ValueError:
    initialize_app(cred)

# Google OAuth2 credentials from Streamlit secrets
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
redirect_url = st.secrets["redirect_url"]

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
        query_params = st.experimental_get_query_params()
        code = query_params.get('code')
        if code:
            token = asyncio.run(get_access_token(client, redirect_url, code[0]))
            st.experimental_set_query_params()

            if token:
                user_id, user_email = asyncio.run(get_email(client, token['access_token']))
                if user_email:
                    try:
                        user = auth.get_user_by_email(user_email)
                    except exceptions.FirebaseError:
                        user = auth.create_user(email=user_email)
                    st.session_state.email = user.email
                    return user.email
        return None
    except Exception as e:
        print(e)
        return None

def show_login_button():
    authorization_url = asyncio.run(client.get_authorization_url(
        redirect_url,
        scope=["email", "profile"],
        extras_params={"access_type": "offline"},
    ))
    st.markdown(f'<a href="{authorization_url}" target="_self">Login</a>', unsafe_allow_html=True)

def app():
    st.title('Smart Lawyer Login Portal')
    if not st.session_state.email:
        get_logged_in_user_email()
        if not st.session_state.email:
            show_login_button()

    if st.session_state.email:
        st.write(f"Logged in as: {st.session_state.email}")
        if st.button("Logout", type="primary", key="logout"):
            st.session_state.email = ''
            st.experimental_rerun()

app()
