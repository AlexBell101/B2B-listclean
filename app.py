
import openai
import streamlit as st
import pandas as pd
import phonenumbers
from io import BytesIO
import pycountry
import re

# Set the page config before any other Streamlit code
st.set_page_config(page_title="List Karma", layout="centered")

# Custom CSS to force light or custom theme even when the user has dark mode enabled
st.markdown(
    """
    <style>
    /* Force light mode or custom theme for both light and dark mode users */
    html, body, [class*="css"]  {
        background-color: #FFFFFF;  /* White background */
        color: #000000;  /* Black text */
        font-family: 'Roboto', sans-serif;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# Helper function for country code conversion (Country Name to ISO Code)
def country_to_code(country_name):
    try:
        return pycountry.countries.lookup(country_name).alpha_2
    except LookupError:
        return country_name

# Helper function for ISO code to full country name conversion
def code_to_country(country_code):
    try:
        return pycountry.countries.get(alpha_2=country_code).name
    except LookupError:
        return country_code

# Function to combine columns based on user selection with an option to retain original column titles
def combine_columns(df):
    st.sidebar.markdown("### Combine Columns")

    # Multiselect to choose columns to combine
    columns_to_combine = st.sidebar.multiselect("Select columns to combine", df.columns)

    if columns_to_combine:
        delimiter = st.sidebar.text_input("Enter a delimiter (optional)", value=", ")
        new_column_name = st.sidebar.text_input("Enter a name for the new combined column", value="Combined Column")
        retain_headings = st.sidebar.checkbox("Retain original column headings in value?")

        if st.sidebar.button("Combine Selected Columns"):
            # Combine the columns with or without retaining the original column names
            if retain_headings:
                df[new_column_name] = df[columns_to_combine].astype(str).apply(
                    lambda row: delimiter.join([f"{col}: {value}" for col, value in zip(columns_to_combine, row.values)]),
                    axis=1
                )
            else:
                df[new_column_name] = df[columns_to_combine].astype(str).apply(
                    lambda row: delimiter.join(row.values), axis=1)
                
            st.success(f"Columns {', '.join(columns_to_combine)} have been combined into '{new_column_name}'")
    return df

# Function to rename columns based on user input
def rename_columns(df):
    st.sidebar.markdown("### Rename Columns")

    # Multiselect to choose columns to rename
    columns_to_rename = st.sidebar.multiselect("Select columns to rename", df.columns)

    if columns_to_rename:
        new_names = {}
        for col in columns_to_rename:
            new_name = st.sidebar.text_input(f"New name for '{col}'", value=col)
            new_names[col] = new_name

        if st.sidebar.button("Rename Selected Columns"):
            df = df.rename(columns=new_names)
            st.success(f"Columns renamed successfully: {new_names}")
    return df

# Other helper functions (for country code conversion, phone cleanup, etc.) would go here

# UI setup for the app
st.title("📋 List Karma")
st.write("Upload your marketing lists and clean them up for CRM tools like Salesforce, Marketo, HubSpot. Use the Karmic AI Prompt if you need a specific transformation applied to your file.")

# File upload logic
uploaded_file = st.file_uploader("Upload your file", type=['csv', 'xls', 'xlsx', 'txt'])

if uploaded_file is not None:
    # File has been uploaded, now we can process it
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file, delimiter="\t")

    st.write("### Data Preview (Before Cleanup):")
    st.dataframe(df.head())

    # Combine columns functionality
    df = combine_columns(df)

    # Rename columns functionality
    df = rename_columns(df)

    # Other cleanup functions and processes would be added here

    st.write("### Data Preview (After Cleanup):")
    st.dataframe(df.head())
