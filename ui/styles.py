"""
UI Styling module for the EV Charging Finder application.

This module provides centralized styling and branding for the Streamlit
interface, including the Virta-inspired design language.

Design language features:
- EV yellow background (#F6E600)
- Black text for high contrast
- Minimal, clean layout with playful elements

Functions in this module ensure consistent visual design across the
entire application.
"""

import streamlit as st


def apply_styles():
    st.markdown("""
    <style>
    .stApp {
        background-color: #F6E600;
    }

    h1 {
        color: black !important;
    }

    label {
        color: black !important;
        font-weight: 600;
    }

    div[data-baseweb="input"] > div {
        background-color: #1f2430;
        border-radius: 10px;
    }

    input {
        color: white !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)