import openai
import streamlit as st
import pandas as pd
import phonenumbers
from io import BytesIO
import pycountry
import re

# Set the page config before any other Streamlit code
st.set_page_config(page_title="List Karma", layout="centered")

# Custom CSS to style the sidebar and select boxes
st.markdown(
    """
    <style>
    /* Custom styles omitted for brevity */
    </style>
    """,
    unsafe_allow_html=True
)

# Create a custom OpenAI API client
client = openai

# Cache OpenAI key loading
@st.cache_resource
def openai_key_loaded()->bool:
    # Fetch the OpenAI API key from Streamlit secrets
    try:
        key = st.secrets["OPENAI_API_KEY"]
        client.api_key = key
    except (FileNotFoundError, KeyError):
        key = None
        st.toast("No OpenAI key Found, LLM functionality will be disabled")
openai_key_loaded()

# List of common personal email domains
personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'outlook.com']

# Step 1: Helper function to standardize country names
def standardize_country_name(country_name):
    return country_name.strip().lower()

# Step 2: Function to convert full country name to ISO 3166-1 alpha-2 code
def country_to_code(country_name):
    standardized_country_name = standardize_country_name(country_name)

    # Check if the input is already a country code (e.g., "US", "DE")
    if len(standardized_country_name) == 2:
        try:
            country = pycountry.countries.get(alpha_2=standardized_country_name.upper())
            return country.alpha_2 if country else country_name
        except LookupError:
            return country_name

    # Otherwise, look it up by full name
    try:
        country = pycountry.countries.lookup(standardized_country_name)
        return country.alpha_2  # Converts full name to alpha-2 code (e.g., "United States" -> "US")
    except LookupError:
        # If lookup fails, return the original input
        return country_name

# Step 3: Function to convert ISO 3166-1 alpha-2 code to full country name
def code_to_country(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code.upper())
        return country.name if country else country_code  # Converts "US" to "United States"
    except LookupError:
        return country_code  # If not found, return original input (could already be a full name or invalid)

# Step 4: Function to convert country data in the DataFrame
def convert_country(df, format_type="Long Form"):
    if 'Country' in df.columns:
        if format_type == "Country Code":
            # Convert full country names to short codes
            df['Country'] = df['Country'].apply(lambda x: country_to_code(x))
        elif format_type == "Long Form":
            # Convert short codes to full country names
            df['Country'] = df['Country'].apply(lambda x: code_to_country(x))
    return df

# Function to clean phone numbers
def clean_phone(phone):
    try:
        parsed_phone = phonenumbers.parse(phone, "US")
        return phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return phone

# Function to extract email domain
def extract_email_domain(df):
    if 'Email' in df.columns:
        df['Domain'] = df['Email'].apply(lambda x: x.split('@')[1] if '@' in x else '')
    return df

# Function to classify email type
def classify_email_type(df):
    if 'Email' in df.columns:
        df['Email Type'] = df['Domain'].apply(lambda domain: 'Personal' if domain in personal_domains else 'Business')
    return df

# Function to remove rows with personal emails
def remove_personal_emails(df):
    return df[df['Domain'].apply(lambda domain: domain not in personal_domains)]

# UI setup for the app
st.title("📋 List Karma")
st.write("Upload your marketing lists and clean them up for CRM tools like Salesforce, Marketo, HubSpot. Use the Karmic AI Prompt if you need a specific transformation applied to your file.")

uploaded_file = st.file_uploader("Upload your file", type=['csv', 'xls', 'xlsx', 'txt'])
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file, delimiter="\t")

    st.write("### Data Preview (Before Cleanup):")
    st.dataframe(df.head())

    # Sidebar options
    st.sidebar.title("Cleanup Options")
    output_format = st.sidebar.radio("Select output format", ('CSV', 'Excel', 'TXT'))
    country_format = st.sidebar.selectbox("Country field format", ["Leave As-Is", "Long Form", "Country Code"])
    phone_cleanup = st.sidebar.checkbox("Standardize phone numbers?")
    normalize_names = st.sidebar.checkbox("Capitalize first letter of names?")
    extract_domain = st.sidebar.checkbox("Extract email domain?")
    
    classify_emails = st.sidebar.checkbox("Classify emails as Personal or Business?")
    remove_personal = st.sidebar.checkbox("Remove rows with Personal emails?")

    # Apply the functions to clean data when button is pressed
    if st.button("Clean the data"):
        if normalize_names and 'Name' in df.columns:
            df['Name'] = df['Name'].str.title()

        if country_format and 'Country' in df.columns:
            df = convert_country(df, country_format)

        if phone_cleanup and 'Phone' in df.columns:
            df['Phone'] = df['Phone'].apply(clean_phone)

        if extract_domain:
            df = extract_email_domain(df)  # Ensure 'Domain' column is created

        if 'Domain' in df.columns:
            df = classify_email_type(df)
        else:
            st.error("The 'Domain' column is missing. Ensure email domain extraction is enabled.")

        if remove_personal:
            df = remove_personal_emails(df)

        # Display cleaned data
        st.write("### Data Preview (After Cleanup):")
        st.dataframe(df.head())
        
        # Download cleaned data
        if output_format == 'CSV':
            st.download_button(label="Download CSV", data=df.to_csv(index=False), file_name="cleaned_data.csv", mime="text/csv")
        elif output_format == 'Excel':
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False)
            writer.save()
            st.download_button(label="Download Excel", data=output.getvalue(), file_name="cleaned_data.xlsx", mime="application/vnd.ms-excel")
        elif output_format == 'TXT':
            st.download_button(label="Download TXT", data=df.to_csv(index=False, sep="\t"), file_name="cleaned_data.txt", mime="text/plain")
