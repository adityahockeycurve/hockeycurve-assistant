# app.py
import streamlit as st
import pandas as pd
from data_loader import DataLoader
from finder import TemplateFinder

def main():
    st.set_page_config(
        page_title="HockeyCurve Template Assistant", 
        page_icon="https://www.hockeycurve.com/images/favicon.svg", # Using official favicon
        layout="wide"
    )
    
    # --- Initialize Components (Cached) ---
    @st.cache_resource
    def init_components():
        """Initializes the data loader and finder once."""
        data_loader = DataLoader()
        if data_loader.authenticate_gspread():
            if data_loader.load_data():
                template_finder = TemplateFinder(data_loader)
                return data_loader, template_finder
        return None, None

    data_loader, template_finder = init_components()
    
    # --- Header ---
    st.title("HockeyCurve Template Assistant")
    st.markdown("*How can I assist with your campaign today?*")
    st.markdown("---")
    
    # --- Search Section ---
    query = st.text_input(
        "Search for templates", 
        placeholder="e.g., fashion, automotive, gaming...",
        label_visibility="collapsed"
    )
    
    # --- Main Logic ---
    if template_finder is None:
        st.error("❌ Failed to initialize. Please check your Google Sheets configuration and refresh.")
    elif query:
        with st.spinner(f"🔍 Finding templates for '{query}'..."):
            recommendations = template_finder.find_similar_templates(query, top_k=20)
            
            if not recommendations.empty:
                st.success(f"Found {len(recommendations)} recommended templates for '**{query}**'")
                st.write("") 

                # --- Create a 3-column grid for the desktop view ---
                col1, col2, col3 = st.columns(3)
                
                # Iterate through recommendations and place them in columns
                for index, row in recommendations.iterrows():
                    # Determine which column to place the card in
                    if index % 3 == 0:
                        with col1:
                            with st.container(border=True):
                                st.subheader(row['Template Name'])
                                st.write(row.get('Description', 'No description available.'))
                                if 'Associated Clients' in row and row['Associated Clients']:
                                    st.caption(f"Previously used by: {row['Associated Clients']}")
                                
                                metric_col1, metric_col2 = st.columns(2)
                                metric_col1.metric("Match Score", f"{row['Similarity Score']}%")
                                metric_col2.metric("Avg. CTR", f"{row.get('avg_ctr', 'N/A')}")

                                preview_url = row.get('Open Preview', '')
                                if pd.notna(preview_url) and str(preview_url).startswith('http'):
                                    st.link_button("🔗 Open Preview", preview_url, use_container_width=True)
                                else:
                                    st.button("No Preview", disabled=True, use_container_width=True)
                    elif index % 3 == 1:
                        with col2:
                            with st.container(border=True):
                                st.subheader(row['Template Name'])
                                st.write(row.get('Description', 'No description available.'))
                                if 'Associated Clients' in row and row['Associated Clients']:
                                    st.caption(f"Previously used by: {row['Associated Clients']}")

                                metric_col1, metric_col2 = st.columns(2)
                                metric_col1.metric("Match Score", f"{row['Similarity Score']}%")
                                metric_col2.metric("Avg. CTR", f"{row.get('avg_ctr', 'N/A')}")

                                preview_url = row.get('Open Preview', '')
                                if pd.notna(preview_url) and str(preview_url).startswith('http'):
                                    st.link_button("🔗 Open Preview", preview_url, use_container_width=True)
                                else:
                                    st.button("No Preview", disabled=True, use_container_width=True)
                    else:
                        with col3:
                            with st.container(border=True):
                                st.subheader(row['Template Name'])
                                st.write(row.get('Description', 'No description available.'))
                                if 'Associated Clients' in row and row['Associated Clients']:
                                    st.caption(f"Previously used by: {row['Associated Clients']}")

                                metric_col1, metric_col2 = st.columns(2)
                                metric_col1.metric("Match Score", f"{row['Similarity Score']}%")
                                metric_col2.metric("Avg. CTR", f"{row.get('avg_ctr', 'N/A')}")
                                
                                preview_url = row.get('Open Preview', '')
                                if pd.notna(preview_url) and str(preview_url).startswith('http'):
                                    st.link_button("🔗 Open Preview", preview_url, use_container_width=True)
                                else:
                                    st.button("No Preview", disabled=True, use_container_width=True)

            else:
                st.warning(f"No matching templates found for '{query}'. Please try rephrasing your query.")
    else:
        st.info("💡 Please enter a search query to find relevant templates.")

if __name__ == "__main__":
    main()
