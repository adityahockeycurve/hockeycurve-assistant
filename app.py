# app.py (Final Polished Version)
import streamlit as st
import pandas as pd
from data_loader import DataLoader
from finder import TemplateFinder

def main():
    # --- Page Configuration (set once at the top) ---
    st.set_page_config(
        page_title="HockeyCurve Template Assistant",
        page_icon="🏒",
        layout="wide"
    )

    # --- Initialize Components (Cached) ---
    # This ensures your powerful DataLoader and TemplateFinder classes are loaded only once.
    @st.cache_resource
    def init_components():
        data_loader = DataLoader()
        # Authenticate and load data within the cached function
        if data_loader.authenticate_gspread():
            if data_loader.load_data():
                template_finder = TemplateFinder(data_loader)
                return data_loader, template_finder
        return None, None

    data_loader, template_finder = init_components()
    
    # --- Gemini-style Header ---
    st.markdown("""
    <style> .centered-title { text-align: center; font-size: 2.5em; font-weight: bold; color: #2c3e50; }
    .centered-subtitle { text-align: center; font-size: 1.2em; color: #888; } </style>
    """, unsafe_allow_html=True)
    st.markdown('<p class="centered-title">HockeyCurve Template Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="centered-subtitle">How can I assist with your campaign today?</p>', unsafe_allow_html=True)
    st.write("")

    # --- Centered Search Bar and Suggestion Buttons ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if 'query' not in st.session_state:
            st.session_state.query = ""

        query = st.text_input(
            "Search Bar",
            value=st.session_state.query,
            placeholder="e.g., e-commerce fashion sale or jewellery campaign",
            label_visibility="collapsed"
        )
        
        # Update the query in session state if the user types
        if query != st.session_state.query:
            st.session_state.query = query
            st.rerun()

    # --- Results Display Section ---
    st.markdown("---")
    
    if data_loader is None or template_finder is None:
        st.error("❌ Failed to initialize or load data from Google Sheets. Please check your credentials and sheet configuration.")
    elif st.session_state.query:
        with st.spinner(f"🔍 Finding templates for '{st.session_state.query}'..."):
            recommendations = template_finder.find_similar_templates(st.session_state.query, top_k=20)
            
            if not recommendations.empty:
                st.success(f"Found {len(recommendations)} recommended templates for '**{st.session_state.query}**'")
                
                # --- Prepare DataFrame for Display ---
                # Rename 'Similarity Score' to 'Match Score'
                recommendations.rename(columns={'Similarity Score': 'Match Score'}, inplace=True)
                
                # --- FIX: Rename the 'Open Preview' column to 'Preview Link' to match the config ---
                recommendations.rename(columns={'Open Preview': 'Preview Link'}, inplace=True)

                # Select and reorder columns
                display_columns = ['Template Name', 'Match Score', 'Description', 'Preview Link']
                display_df = recommendations.loc[:, [col for col in display_columns if col in recommendations.columns]].copy()

                # Format the Match Score for display
                display_df['Match Score'] = display_df['Match Score'].apply(lambda x: f"{round(x)}%")

                # Display the final, clean table
                st.data_editor(
                    display_df,
                    column_config={
                        "Preview Link": st.column_config.LinkColumn("Open Preview")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.warning(f"No matching templates found for '{st.session_state.query}'. Please try rephrasing your query.")
    else:
        # Display suggestion buttons only if there is no active query
        st.info("💡 Try a search above or use a quick suggestion:")
        suggestion_cols = st.columns(4)
        suggestions = ["FMCG Launch", "Banking Offers", "Automotive EV", "Gaming Templates"]
        for i, suggestion in enumerate(suggestions):
            if suggestion_cols[i].button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                st.session_state.query = suggestion
                st.rerun()

if __name__ == "__main__":
    main()