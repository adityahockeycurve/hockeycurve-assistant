# data_loader.py
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

class DataLoader:
    def __init__(self):
        self.gc = None
        self.client_profiles = None
        self.template_tags = None
        self.template_details = None
        
        # Configuration
        self.SPREADSHEET_ID = "1WaY3H_T8rAtHvLSmJ_MvqVvzy5MEaEqLbdUxDeVh228"
        
    def authenticate_gspread(self, credentials_path=None):
        """Authenticate with Google Sheets API"""
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            # Use Streamlit secrets when deployed
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=scope
            )
            self.gc = gspread.authorize(creds)
            return True
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return False
    
    def load_data(self):
        """Load data from Google Sheets"""
        try:
            # Open the spreadsheet
            spreadsheet = self.gc.open_by_key(self.SPREADSHEET_ID)
            
            # Load Client Profiles
            client_sheet = spreadsheet.worksheet("Client_Profiles")
            client_data = client_sheet.get_all_records()
            self.client_profiles = pd.DataFrame(client_data)
            
            # Load Template Tags and Previews
            template_tags_sheet = spreadsheet.worksheet("Template_Tags_and_Previews")
            template_tags_data = template_tags_sheet.get_all_records()
            self.template_tags = pd.DataFrame(template_tags_data)
            
            # Load Template Details
            template_details_sheet = spreadsheet.worksheet("Template_Details")
            template_details_data = template_details_sheet.get_all_records()
            self.template_details = pd.DataFrame(template_details_data)
            
            # Basic data validation
            self._validate_data()
            
            return True
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return False
    
    def _validate_data(self):
        """Validate that required columns exist in the data"""
        required_client_cols = ['client_type', 'keywords', 'domain_url', 'industry', 
                               'business_niche', 'marketing_focus', 'relevant_keywords']
        if not all(col in self.client_profiles.columns for col in required_client_cols):
            st.warning("One or more required columns are missing in 'Client_Profiles'.")

        required_tags_cols = ['campaign_name', 'client_name', 'template_name']
        if not all(col in self.template_tags.columns for col in required_tags_cols):
            st.warning("One or more required columns are missing in 'Template_Tags_and_Previews'.")

        required_details_cols = ['template_name', 'description', 'avg_ctr', 'preview_url']
        if not all(col in self.template_details.columns for col in required_details_cols):
            st.warning("One or more required columns are missing in 'Template_Details'.")
    
    def get_client_profiles(self):
        return self.client_profiles
    
    def get_template_tags(self):
        return self.template_tags
    
    def get_template_details(self):
        return self.template_details
