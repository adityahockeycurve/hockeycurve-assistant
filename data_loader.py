# data_loader.py (Final Corrected Version)
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

@st.cache_resource(show_spinner="Initializing Assistant, please wait...")
def load_and_process_data():
    """
    This function loads all data, merges it, creates all necessary text fields
    for searching, and builds the search index.
    """
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        spreadsheet = client.open(MASTER_SHEET_NAME)

        profiles_sheet = spreadsheet.worksheet(SHEET_NAMES['profiles'])
        details_sheet = spreadsheet.worksheet(SHEET_NAMES['details'])
        campaigns_sheet = spreadsheet.worksheet(SHEET_NAMES['campaigns'])

        profiles_df = pd.DataFrame(profiles_sheet.get_all_records())
        templates_df = pd.DataFrame(details_sheet.get_all_records())
        campaigns_df = pd.DataFrame(campaigns_sheet.get_all_records())

        # Merge campaign data into the main templates dataframe
        master_df = pd.merge(templates_df, campaigns_df.drop_duplicates(subset=['template_name']), on='template_name', how='left')
        
        # --- ROBUST FIX FOR PREVIEW URL ---
        # Consolidate preview URLs if they exist in either of the merged tables
        if 'preview_url_y' in master_df.columns and 'preview_url_x' in master_df.columns:
            master_df['preview_url'] = master_df['preview_url_y'].fillna(master_df['preview_url_x'])
        elif 'preview_url_x' in master_df.columns:
            master_df['preview_url'] = master_df['preview_url_x']
        elif 'preview_url_y' in master_df.columns:
            master_df['preview_url'] = master_df['preview_url_y']
        
        # Clean the CTR column robustly
        def _clean_ctr(value):
            if pd.isna(value) or value == '': return 0.0
            try: return float(str(value).split('-')[0].replace('%', '').strip())
            except (ValueError, TypeError): return 0.0
        
        master_df['ctr_value'] = master_df['avg_ctr'].apply(_clean_ctr)

        # Create the searchable text field
        master_df['searchable_text'] = (
            master_df['template_name'].fillna('').str.lower() + ' ' +
            master_df['description'].fillna('').str.lower() + ' ' +
            master_df.get('campaign_name', '').fillna('').str.lower() + ' ' +
            master_df.get('client_name', '').fillna('').str.lower()
        )
        
        # --- Build the search index ---
        search_index = defaultdict(list)
        for index, row in master_df.iterrows():
            # Normalize text for the index
            normalized_text = re.sub(r'[^a-z0-9\s]', '', row['searchable_text'])
            normalized_text = re.sub(r'\s+', ' ', normalized_text).strip()
            unique_words = set(normalized_text.split())
            for word in unique_words:
                if word: search_index[word].append(index)
        
        print("Data loaded and definitive search index created!")
        return master_df, profiles_df, search_index

    except Exception as e:
        st.error(f"An error occurred during data loading: {e}")
        return None, None, None