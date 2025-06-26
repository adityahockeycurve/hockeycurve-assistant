# data_loader.py (Deployment-Ready Version)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
from collections import defaultdict
import re

SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'credentials.json'
MASTER_SHEET_NAME = 'HockeyCurve_Master_Data'
SHEET_NAMES = {
    'profiles': 'Client_Profiles',
    'details': 'Template_Details',
    'campaigns': 'Template_Tags_and_Previews'
}

def _get_creds():
    """
    This function smartly gets credentials. It tries Streamlit's secrets first
    (for cloud deployment) and falls back to the local JSON file.
    """
    try:
        # For deployed app, use Streamlit's secrets management
        creds_dict = st.secrets["gcp_service_account"]
        return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    except (FileNotFoundError, KeyError):
        # For local development, use the credentials.json file
        return ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)

@st.cache_resource(show_spinner="Initializing Assistant, please wait...")
def load_and_process_data():
    """
    Loads all data using the smart credential handler and builds the index.
    """
    try:
        creds = _get_creds()
        client = gspread.authorize(creds)
        spreadsheet = client.open(MASTER_SHEET_NAME)

        profiles_sheet = spreadsheet.worksheet(SHEET_NAMES['profiles'])
        details_sheet = spreadsheet.worksheet(SHEET_NAMES['details'])
        campaigns_sheet = spreadsheet.worksheet(SHEET_NAMES['campaigns'])

        profiles_df = pd.DataFrame(profiles_sheet.get_all_records())
        templates_df = pd.DataFrame(details_sheet.get_all_records())
        campaigns_df = pd.DataFrame(campaigns_sheet.get_all_records())
        
        # (The rest of the data processing logic remains the same)
        master_df = pd.merge(templates_df, campaigns_df.drop_duplicates(subset=['template_name']), on='template_name', how='left')
        
        if 'preview_url_y' in master_df.columns and 'preview_url_x' in master_df.columns:
            master_df['preview_url'] = master_df['preview_url_y'].fillna(master_df['preview_url_x'])
        elif 'preview_url_x' in master_df.columns:
             master_df['preview_url'] = master_df['preview_url_x']
        elif 'preview_url_y' in master_df.columns:
             master_df['preview_url'] = master_df['preview_url_y']

        def _clean_ctr(value):
            if pd.isna(value) or value == '': return 0.0
            try: return float(str(value).split('-')[0].replace('%', '').strip())
            except (ValueError, TypeError): return 0.0
        
        master_df['avg_ctr'] = master_df['avg_ctr'].apply(_clean_ctr)
        master_df.rename(columns={'avg_ctr': 'ctr_value'}, inplace=True)

        master_df['searchable_text'] = (
            master_df['template_name'].fillna('').str.lower() + ' ' +
            master_df['description'].fillna('').str.lower() + ' ' +
            master_df.get('campaign_name', '').fillna('').str.lower() + ' ' +
            master_df.get('client_name', '').fillna('').str.lower()
        )
        
        search_index = defaultdict(list)
        for index, row in master_df.iterrows():
            normalized_text = re.sub(r'[^a-z0-9\s]', '', row['searchable_text'])
            unique_words = set(normalized_text.split())
            for word in unique_words:
                if word: search_index[word].append(index)
        
        print("Data loaded and definitive search index created!")
        return master_df, profiles_df, search_index

    except Exception as e:
        st.error(f"An error occurred during data loading: {e}")
        return None, None, None