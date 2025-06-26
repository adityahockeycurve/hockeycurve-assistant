# app.py (Final Polished UI with All Fixes)
import streamlit as st
import pandas as pd
from data_loader import load_and_process_data
from finder import find_best_templates

st.set_page_config(
    page_title="HockeyCurve Template Assistant",
    page_icon="🏒",
    layout="wide"
)

# Load data with the startup spinner message
templates_df, profiles_df, search_index = load_and_process_data()

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

    user_query = st.text_input("Search Bar", value=st.session_state.query, placeholder="e.g., awareness campaign for FMCG", label_visibility="collapsed")

    sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)
    if sub_col1.button("FMCG Launch", use_container_width=True): st.session_state.query = "New product launch for FMCG"; st.rerun()
    if sub_col2.button("Banking Offers", use_container_width=True): st.session_state.query = "Credit card offer for banking"; st.rerun()
    if sub_col3.button("Automotive EV", use_container_width=True): st.session_state.query = "New EV car launch for automotive"; st.rerun()
    if sub_col4.button("Gaming Templates", use_container_width=True): st.session_state.query = "Gamified ad for mobile game"; st.rerun()
        
    if user_query != st.session_state.query:
        st.session_state.query = user_query
        st.rerun()

st.markdown("---")

# --- Results Display Section ---
if templates_df is None or profiles_df is None:
    st.error("Could not load data. Please verify your Google Sheet settings and refresh.")
else:
    if st.session_state.query:
        results = find_best_templates(st.session_state.query, templates_df, profiles_df, search_index)

        if results:
            st.success(f"Found {len(results)} recommended templates for **'{st.session_state.query}'**")
            
            results_df = pd.DataFrame([res['data'] for res in results])
            
            display_columns = ['template_name', 'avg_ctr', 'description', 'preview_url']
            display_df = results_df.loc[:, [col for col in display_columns if col in results_df.columns]].copy()
            
            rename_mapping = {
                'template_name': 'Template Name', 'avg_ctr': 'Avg CTR',
                'description': 'Description', 'preview_url': 'Preview Link'
            }
            display_df.rename(columns=rename_mapping, inplace=True)

            # --- RESTORED st.data_editor for clean table and short links ---
            st.data_editor(
                display_df,
                column_config={
                    "Preview Link": st.column_config.LinkColumn(
                        "Open Preview",
                        help="Click to see a live preview of the ad template"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning("No matching templates found. Please try rephrasing your query or using broader keywords.")