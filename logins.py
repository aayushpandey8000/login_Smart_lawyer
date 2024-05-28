import streamlit as st
import firebase_admin
from firebase_admin import auth, credentials, initialize_app
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2

# Set the background image
background_image = """
<style>
[data-testid="stAppViewContainer"] > .main {
    background-image: url("https://i.ibb.co/rwQBRdJ/magicpattern-mesh-gradient-1715094470100.png");
    background-size: 100vw 100vh;  # This sets the size to cover 100% of the viewport width and height
    background-position: center;  
    background-repeat: no-repeat;
}
</style>
"""

st.markdown(background_image, unsafe_allow_html=True)

# Custom input styling
input_style = """
<style>
textarea {
    background-color: white;
    color: #FFFFFF; /* Change to the desired text color */
    border-radius: 5px; /* Optional: Adjust border radius for rounded corners */
}
div[data-baseweb="base-input"] {
    background-color: transparent !important;
}
[data-testid="stAppViewContainer"] {
    background-color: transparent !important;
}
</style>
"""

st.markdown(input_style, unsafe_allow_html=True)

# Initialize Firebase app
if not firebase_admin._apps:
    cred = credentials.Certificate(st.secrets["firebase"])
    initialize_app(cred)

# Google OAuth2 credentials
client_id = st.secrets["google"]["client_id"]
client_secret = st.secrets["google"]["client_secret"]
redirect_url = "https://smart-lawyer-007.streamlit.app/"

# Initialize Google OAuth2 client
client = GoogleOAuth2(client_id=client_id, client_secret=client_secret)

if "email" not in st.session_state:
    st.session_state.email = ''

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
                    except firebase_admin._auth_utils.UserNotFoundError:
                        user = auth.create_user(email=user_email)
                    st.session_state.email = user.email
                    return user.email
        return None
    except Exception as e:
        st.error(f"Error during login: {str(e)}")
        return None

def show_login_button():
    authorization_url = asyncio.run(client.get_authorization_url(
        redirect_url,
        scope=["email", "profile"],
        extras_params={"access_type": "offline"},
    ))
    st.markdown(f'<a href="{authorization_url}" target="_self">Login</a>', unsafe_allow_html=True)
    get_logged_in_user_email()

def app():
    st.title('Smart Lawyer Login Portal')
    if not st.session_state.email:
        get_logged_in_user_email()
        if not st.session_state.email:
            show_login_button()
    else:
        st.write(f"Welcome, {st.session_state.email}!")
        # Your main app content goes here
        # For example, provide access to other features only if logged in
        if st.button("Logout"):
            st.session_state.email = ''
            st.experimental_rerun()

# Run the app
app()
