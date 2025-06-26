# debug_app.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Page Config ---
st.set_page_config(page_title="Streamlit Connection Debugger")
st.header("Streamlit & Google Sheets Connection Debugger")
st.write("This app will test each step of the connection process.")

# --- Step 1: Check for Secrets ---
st.markdown("---")
st.subheader("Step 1: Checking for Streamlit Secrets")

try:
    secrets_dict = st.secrets["gcp_service_account"]
    st.success("✅ Success: `gcp_service_account` secret found!")
    # To be safe, let's check for a key key
    if "private_key" in secrets_dict:
        st.info("`private_key` exists within the secret.")
    else:
        st.error("❌ Error: `private_key` key is MISSING from the secret. Please check your TOML format.")
        st.stop()
except (KeyError, FileNotFoundError):
    st.error("❌ Fatal Error: `st.secrets['gcp_service_account']` not found. The secret is either missing, not saved, or has the wrong section name in the TOML file. The main heading must be `[gcp_service_account]`.")
    st.stop()


# --- Step 2: Attempt to Authorize with Google ---
st.markdown("---")
st.subheader("Step 2: Authorizing with Google Credentials")

try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(secrets_dict, scope)
    client = gspread.authorize(creds)
    st.success("✅ Success: Credentials authorized with Google!")
except Exception as e:
    st.error("❌ Fatal Error: Credentials were found but FAILED to authorize with Google.")
    st.write("This usually means one of two things:")
    st.write("1. The Google Sheets API or Google Drive API is NOT enabled in your Google Cloud Project.")
    st.write("2. The credentials themselves are invalid (e.g., from a deleted service account).")
    st.exception(e)
    st.stop()

# --- Step 3: Attempt to Open the Google Sheet ---
st.markdown("---")
st.subheader("Step 3: Opening the Google Sheet by Name")
MASTER_SHEET_NAME = 'HockeyCurve_Master_Data'

try:
    spreadsheet = client.open(MASTER_SHEET_NAME)
    st.success(f"✅ Success: Opened Google Sheet named '{MASTER_SHEET_NAME}'!")
except Exception as e:
    st.error(f"❌ Fatal Error: Could not open the spreadsheet named '{MASTER_SHEET_NAME}'.")
    st.write("This usually means one of two things:")
    st.write("1. The name of your Google Sheet file does not exactly match what's in the code.")
    st.write("2. You have not shared the sheet with the `client_email` from your credentials.")
    st.exception(e)
    st.stop()

# --- Step 4: Final Confirmation ---
st.markdown("---")
st.balloons()
st.header("🎉 Congratulations! Connection is working perfectly!")
st.write("If you can see this message, your secrets, APIs, and sharing settings are all correct. You can now switch the 'Main file path' in your settings back to `app.py`.")