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
            
            if credentials_path:
                # If using service account JSON file
                creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
                self.gc = gspread.authorize(creds)
            else:
                # If using streamlit secrets
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
        # Check Client_Profiles columns
        required_client_cols = ['client_type', 'keywords', 'domain_url', 'industry', 
                               'business_niche', 'marketing_focus', 'relevant_keywords']
        missing_client_cols = [col for col in required_client_cols if col not in self.client_profiles.columns]
        if missing_client_cols:
            st.warning(f"Missing columns in Client_Profiles: {missing_client_cols}")
        
        # Check Template_Tags_and_Previews columns
        required_template_tags_cols = ['campaign_name', 'client_name', 
                                      'template_name']
        missing_template_tags_cols = [col for col in required_template_tags_cols if col not in self.template_tags.columns]
        if missing_template_tags_cols:
            st.warning(f"Missing columns in Template_Tags_and_Previews: {missing_template_tags_cols}")
        
        # Check Template_Details columns
        required_template_details_cols = ['template_name', 'description', 'avg_ctr', 'preview_url']
        missing_template_details_cols = [col for col in required_template_details_cols if col not in self.template_details.columns]
        if missing_template_details_cols:
            st.warning(f"Missing columns in Template_Details: {missing_template_details_cols}")
    
    def get_client_profiles(self):
        """Return client profiles dataframe"""
        return self.client_profiles
    
    def get_template_tags(self):
        """Return template tags dataframe"""
        return self.template_tags
    
    def get_template_details(self):
        """Return template details dataframe"""
        return self.template_details
    
    def refresh_data(self):
        """Refresh data from Google Sheets"""
        return self.load_data()
    
    def get_data_summary(self):
        """Get summary of loaded data"""
        if self.client_profiles is None or self.template_tags is None or self.template_details is None:
            return "No data loaded"
        
        summary = {
            "client_profiles_count": len(self.client_profiles),
            "template_tags_count": len(self.template_tags),
            "template_details_count": len(self.template_details),
            "unique_templates": len(self.template_details['template_name'].unique()) if 'template_name' in self.template_details.columns else 0,
            "unique_clients": len(self.template_tags['client_name'].unique()) if 'client_name' in self.template_tags.columns else 0
        }
        return summary