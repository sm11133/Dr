import streamlit as st
import os
import io
import pickle
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title="📤 Google Drive Upload", page_icon="📁")
st.title("📁 Upload File to Google Drive via Streamlit UI")

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_FILE = "token.pickle"
CREDENTIALS_FILE = "credentials.json"
FOLDER_ID = "1lVsJ3-CjtgKaAyBszmaDWEC6MaOVpZwV"  # ← अपना Drive Folder ID

# ----------------------------
# Function: Get Drive Service
# ----------------------------
@st.cache_resource
def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds:
        return None

    service = build("drive", "v3", credentials=creds)
    return service

# ----------------------------
# UI: Handle Auth
# ----------------------------
if not os.path.exists(TOKEN_FILE):
    if os.path.exists(CREDENTIALS_FILE):
        st.info("🔐 Please authorize the app to access your Google Drive.")

        auth_flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri="urn:ietf:wg:oauth:2.0:oob"
        )
        auth_url, _ = auth_flow.authorization_url(prompt='consent')

        st.markdown(f"👉 [Click here to authorize your Google account]({auth_url})", unsafe_allow_html=True)
        auth_code = st.text_input("🔑 Paste the authorization code here:")

        if auth_code:
            try:
                auth_flow.fetch_token(code=auth_code)
                creds = auth_flow.credentials
                with open(TOKEN_FILE, "wb") as token:
                    pickle.dump(creds, token)
                st.success("✅ Authorization successful! Reload the app.")
                st.stop()
            except Exception as e:
                st.error(f"❌ Authorization failed: {e}")
                st.stop()
    else:
        st.error("❌ credentials.json not found!")
        st.stop()

# ----------------------------
# If Auth Successful → Show Upload
# ----------------------------
drive_service = get_drive_service()
if not drive_service:
    st.warning("⚠️ App not authorized yet.")
    st.stop()

uploaded_file = st.file_uploader("📂 Upload any file to Google Drive")

if uploaded_file is not None:
    st.info(f"📤 Uploading `{uploaded_file.name}`...")

    file_metadata = {
        'name': uploaded_file.name,
        'parents': [FOLDER_ID]
    }
    media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)

    try:
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        st.success("✅ File uploaded successfully!")
        st.markdown(f"[🔗 Open File](https://drive.google.com/file/d/{file['id']})", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Upload failed: {e}")