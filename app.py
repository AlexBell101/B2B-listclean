import openai
import streamlit as st
import pandas as pd
import phonenumbers
from io import BytesIO
import pycountry
import re
from streamlit_cookies_manager import EncryptedCookieManager

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

# Initialize a cookie manager with encryption
cookies = EncryptedCookieManager(
    prefix="list_karma_", 
    password="your_secret_password"  # Replace with a secure password
)

if not cookies.ready():
    st.stop()

# Function to save user settings to cookies
def save_configuration_to_cookie(config):
    cookies["user_config"] = config
    cookies.save()

# Function to load user settings from cookies
def load_configuration_from_cookie():
    return cookies.get("user_config", {})

# Default configuration options for the app
default_config = {
    "output_format": "CSV",
    "country_format": "Long Form",
    "phone_cleanup": True,
    "extract_domain": False,
}

# Load configuration from cookies or fallback to default
config = load_configuration_from_cookie() or default_config

# File upload logic and initial preview
uploaded_file = st.file_uploader("Upload your file", type=['csv', 'xls', 'xlsx', 'txt'])
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file, delimiter="\t")
    
    # Display uploaded data preview
    st.write("### Data Preview (Before Cleanup):")
    st.dataframe(df.head())
    
# Sidebar options (loaded from cookies or default config)
st.sidebar.title("Cleanup Options")
output_format = st.sidebar.radio("Select output format", ('CSV', 'Excel', 'TXT'), index=['CSV', 'Excel', 'TXT'].index(config['output_format']))
country_format = st.sidebar.selectbox("Country field format", ["Leave As-Is", "Long Form", "Country Code"], index=["Leave As-Is", "Long Form", "Country Code"].index(config['country_format']))
phone_cleanup = st.sidebar.checkbox("Standardize phone numbers?", value=config['phone_cleanup'])
extract_domain = st.sidebar.checkbox("Extract email domain?", value=config['extract_domain'])
normalize_names = st.sidebar.checkbox("Capitalize first letter of names?")

# Additional options
classify_emails = st.sidebar.checkbox("Classify emails as Personal or Business?")
remove_personal = st.sidebar.checkbox("Remove rows with Personal emails?")
clean_address = st.sidebar.checkbox("Clean up and separate Address fields?")
split_city_state_option = st.sidebar.checkbox("Split combined City and State fields?")
add_lead_source = st.sidebar.checkbox("Add 'Lead Source' field?")
lead_source_value = st.sidebar.text_input("Lead Source Value") if add_lead_source else None
add_lead_source_detail = st.sidebar.checkbox("Add 'Lead Source Detail' field?")
lead_source_detail_value = st.sidebar.text_input("Lead Source Detail Value") if add_lead_source_detail else None
add_campaign = st.sidebar.checkbox("Add 'Campaign' field?")
campaign_value = st.sidebar.text_input("Campaign Value") if add_campaign else None
split_by_status = st.sidebar.checkbox("Split output by 'Status' column?")
status_column = st.sidebar.selectbox("Select Status Column", df.columns) if split_by_status else None

# Input for custom file name
custom_file_name = st.sidebar.text_input("Custom File Name (without extension)", value="cleaned_data")

# Save configuration button
if st.sidebar.button("Save Configuration"):
    config = {
        "output_format": output_format,
        "country_format": country_format,
        "phone_cleanup": phone_cleanup,
        "extract_domain": extract_domain,
    }
    save_configuration_to_cookie(config)
    st.success("Configuration saved to cookies!")

# List of common personal email domains
personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'outlook.com']

# Function to combine columns
def combine_columns(df, columns_to_combine, delimiter, new_column_name, retain_headings, remove_original):
    if columns_to_combine:
        if retain_headings:
            df[new_column_name] = df[columns_to_combine].astype(str).apply(
                lambda row: delimiter.join([f"{col}: {value}" for col, value in zip(columns_to_combine, row.values)]),
                axis=1
            )
        else:
            df[new_column_name] = df[columns_to_combine].astype(str).apply(lambda row: delimiter.join(row.values), axis=1)

        # Remove original columns if the user chooses to do so
        if remove_original:
            df = df.drop(columns=columns_to_combine)

        st.success(f"Columns {', '.join(columns_to_combine)} have been combined into '{new_column_name}'")
    
    return df

# Functions for phone, address, and country transformations
def clean_phone(phone):
    try:
        parsed_phone = phonenumbers.parse(phone, "US")
        return phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return phone

def split_address_2(df):
    if 'Address' in df.columns:
        df['Address 1'] = df['Address'].apply(lambda x: re.split(r'(?i)\b(Apt|Unit|Suite)\b', x)[0].strip())
        df['Address 2'] = df['Address'].apply(lambda x: re.search(r'(?i)(Apt|Unit|Suite).*', x).group(0) if re.search(r'(?i)(Apt|Unit|Suite).*', x) else "")
    return df

def split_city_state(df):
    if 'City_State' in df.columns:
        df[['City', 'State']] = df['City_State'].str.split(',', 1, expand=True)
        df['City'] = df['City'].str.strip()
        df['State'] = df['State'].str.strip()
    return df

def extract_email_domain(df):
    if 'Email' in df.columns:
        df['Domain'] = df['Email'].apply(lambda x: x.split('@')[1] if '@' in x else '')
    return df

def classify_email_type(df, personal_domains):
    if 'Domain' in df.columns:
        df['Email Type'] = df['Domain'].apply(lambda domain: 'Personal' if domain in personal_domains else 'Business')
    return df

def remove_personal_emails(df, personal_domains):
    return df[df['Domain'].apply(lambda domain: domain not in personal_domains)]

# Function to clean and transform the data based on the selected options
if st.button("Clean the data"):
    # Normalize names
    if normalize_names and 'Name' in df.columns:
        df['Name'] = df['Name'].str.title()

    # Convert country column based on selected format
    if 'Country' in df.columns:
        df = convert_country(df, country_format)

    # Clean phone numbers
    if phone_cleanup and 'Phone' in df.columns:
        df['Phone'] = df['Phone'].apply(clean_phone)

    if extract_domain:
        df = extract_email_domain(df)

    if classify_emails:
        df = classify_email_type(df, personal_domains)

    if remove_personal:
        df = remove_personal_emails(df, personal_domains)

    # Clean and split addresses
    if clean_address:
        df = split_address_2(df)
    if split_city_state_option:
        df = split_city_state(df)

    # Add additional columns (Lead Source, Campaign, etc.)
    if add_lead_source:
        df['Lead Source'] = lead_source_value
    if add_lead_source_detail:
        df['Lead Source Detail'] = lead_source_detail_value
    if add_campaign:
        df['Campaign'] = campaign_value

    # Display cleaned data
    st.write("### Data Preview (After Cleanup):")
    st.dataframe(df.head())

    # Handle file output and downloads
    if split_by_status and status_column:
        unique_status_values = df[status_column].unique()
        for status_value in unique_status_values:
            status_df = df[df[status_column] == status_value]
            st.write(f"#### Data for Status {status_value}")
            st.dataframe(status_df.head())

            if output_format == 'CSV':
                file_name = f"{custom_file_name}_{status_value}.csv"
                st.download_button(label=f"Download CSV for {status_value}",
                                   data=status_df.to_csv(index=False),
                                   file_name=file_name,
                                   mime="text/csv")
            elif output_format == 'Excel':
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                status_df.to_excel(writer, index=False)
                writer.save()
                file_name = f"{custom_file_name}_{status_value}.xlsx"
                st.download_button(label=f"Download Excel for {status_value}",
                                   data=output.getvalue(),
                                   file_name=file_name,
                                   mime="application/vnd.ms-excel")
            elif output_format == 'TXT':
                file_name = f"{custom_file_name}_{status_value}.txt"
                st.download_button(label=f"Download TXT for {status_value}",
                                   data=status_df.to_csv(index=False, sep="\t"),
                                   file_name=file_name,
                                   mime="text/plain")
    else:
        if output_format == 'CSV':
            file_name = f"{custom_file_name}.csv"
            st.download_button(label="Download CSV", data=df.to_csv(index=False),
                               file_name=file_name, mime="text/csv")
        elif output_format == 'Excel':
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False)
            writer.save()
            file_name = f"{custom_file_name}.xlsx"
            st.download_button(label="Download Excel", data=output.getvalue(),
                               file_name=file_name, mime="application/vnd.ms-excel")
        elif output_format == 'TXT':
            file_name = f"{custom_file_name}.txt"
            st.download_button(label="Download TXT", data=df.to_csv(index=False, sep="\t"),
                               file_name=file_name, mime="text/plain")
