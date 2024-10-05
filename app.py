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

# UI setup for the app
st.title("📋 List Karma")
st.write("Upload your marketing lists and clean them up for CRM tools like Salesforce, Marketo, HubSpot. Use the Karmic AI Prompt if you need a specific transformation applied to your file.")

# Create a custom OpenAI API client
client = openai

# Fetch the OpenAI API key from Streamlit secrets
client.api_key = st.secrets["OPENAI_API_KEY"]

# List of common personal email domains
personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'outlook.com']

# Function to combine columns based on user selection with an option to retain original column titles and remove original columns
def combine_columns(df, columns_to_combine, delimiter, new_column_name, retain_headings, remove_original):
    if columns_to_combine:
        if retain_headings:
            df[new_column_name] = df[columns_to_combine].astype(str).apply(
                lambda row: delimiter.join([f"{col}: {value}" for col, value in zip(columns_to_combine, row.values)]),
                axis=1
            )
        else:
            df[new_column_name] = df[columns_to_combine].astype(str).apply(
                lambda row: delimiter.join(row.values), axis=1)

        # Remove original columns if the user chooses to do so
        if remove_original:
            df = df.drop(columns=columns_to_combine)

        st.success(f"Columns {', '.join(columns_to_combine)} have been combined into '{new_column_name}'")
    
    return df

# Function to rename columns based on user input
def rename_columns(df, new_names):
    df = df.rename(columns=new_names)
    return df

# Function to convert country name to ISO code or vice versa based on format_type
def convert_country(df, format_type="Long Form"):
    if 'Country' in df.columns:
        if format_type == "Country Code":
            df['Country'] = df['Country'].apply(lambda x: country_to_code(x) if pd.notnull(x) else x)
        elif format_type == "Long Form":
            df['Country'] = df['Country'].apply(lambda x: code_to_country(country_to_code(x)) if pd.notnull(x) else x)
    return df

# Function to capitalize the first letter of each word in the Name column
def capitalize_names(df):
    if 'Name' in df.columns:
        df['Name'] = df['Name'].str.title()
        st.success("Capitalized the first letter of each word in the 'Name' column")
    else:
        st.error("'Name' column not found in the dataframe")
    return df
    
# Function to separate first and last name
def split_first_last_name(df, full_name_column):
    if full_name_column in df.columns:
        df['First Name'] = df[full_name_column].apply(lambda x: x.split()[0] if isinstance(x, str) else "")
        df['Last Name'] = df[full_name_column].apply(lambda x: " ".join(x.split()[1:]) if isinstance(x, str) else "")
        st.success(f"Column '{full_name_column}' has been split into 'First Name' and 'Last Name'")
    else:
        st.error(f"'{full_name_column}' not found in columns")
    return df

# Upload file and load the DataFrame
uploaded_file = st.file_uploader("Upload your file", type=['csv', 'xls', 'xlsx', 'txt'])
if uploaded_file is not None:
    # Load the file into a DataFrame `df`
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file, delimiter="\t")
    
    st.write("### Data Preview (Before Cleanup):")
    st.dataframe(df.head())
    
    # Sidebar setup with collapsible sections
    st.sidebar.title("Cleanup Options")

    # === NEW: Only show the column operations if `df` is defined ===
    if df is not None and not df.empty:  # Ensure `df` exists and is not empty

        # === Column Operations Section ===
        with st.sidebar.expander("Column Operations"):
            # Combine columns functionality
            columns_to_combine = st.multiselect("Select columns to combine", df.columns)
            delimiter = st.text_input("Enter a delimiter (optional)", value=", ")
            new_column_name = st.text_input("Enter a name for the new combined column", value="Combined Column")
            retain_headings = st.checkbox("Retain original column headings in value?")
            remove_original = st.checkbox("Remove original columns after combining?")

            # Combine columns button logic
            if st.button("Combine Selected Columns"):
                if columns_to_combine:  # Ensure columns are selected
                    df = combine_columns(df, columns_to_combine, delimiter, new_column_name, retain_headings, remove_original)
                else:
                    st.warning("Please select columns to combine.")
            
            # Rename columns functionality
            columns_to_rename = st.multiselect("Select columns to rename", df.columns)
            new_names = {col: st.text_input(f"New name for '{col}'", value=col) for col in columns_to_rename}
            
            # Rename columns button logic
            if st.button("Rename Selected Columns"):
                if columns_to_rename:
                    df = rename_columns(df, new_names)
                else:
                    st.warning("Please select columns to rename.")

            # Split First and Last Name functionality
            full_name_column = st.selectbox("Select the Full Name column to split", df.columns)
            if st.button("Split First and Last Name"):
                df = split_first_last_name(df, full_name_column)

        # === Data Cleanup Section ===
        with st.sidebar.expander("Data Cleanup"):
            phone_cleanup = st.checkbox("Standardize phone numbers?")
            normalize_names = st.checkbox("Capitalize first letter of names?")
            extract_domain = st.checkbox("Extract email domain?")
            classify_emails = st.checkbox("Classify emails as Personal or Business?")
            remove_personal = st.checkbox("Remove rows with Personal emails?")
            clean_address = st.checkbox("Clean up and separate Address fields?")
            split_city_state_option = st.checkbox("Split combined City and State fields?")
            country_format = st.selectbox("Country field format", ["Leave As-Is", "Long Form", "Country Code"])

        # === Custom Fields Section ===
        with st.sidebar.expander("Custom Fields"):
            add_lead_source = st.checkbox("Add 'Lead Source' field?")
            lead_source_value = st.text_input("Lead Source Value") if add_lead_source else None
            add_lead_source_detail = st.checkbox("Add 'Lead Source Detail' field?")
            lead_source_detail_value = st.text_input("Lead Source Detail Value") if add_lead_source_detail else None
            add_campaign = st.checkbox("Add 'Campaign' field?")
            campaign_value = st.text_input("Campaign Value") if add_campaign else None

        # === Advanced Transformations Section ===
        with st.sidebar.expander("Advanced Transformations"):
            custom_request = st.text_area("Karmic AI Prompt")

        # === Custom File Name Section ===
        custom_file_name = st.sidebar.text_input("Custom File Name (without extension)", value="cleaned_data")

        # === Output Format Section ===
        output_format = st.sidebar.selectbox("Select output format", ['CSV', 'Excel', 'TXT'])

        # Clean the data and apply transformations
        if st.button("Clean the data"):
            # Normalize names
            if normalize_names and 'Name' in df.columns:
                df = capitalize_names(df)
                
            # Split full name into first and last name
            if 'Full Name' in df.columns:
                df = split_first_last_name(df, 'Full Name')  # Assuming 'Full Name' is the column name
            
            # Convert country column based on selected format
            if 'Country' in df.columns:
                df = convert_country(df, country_format)

            # Clean phone numbers
            if phone_cleanup and 'Phone' in df.columns:
                df['Phone'] = df['Phone'].apply(clean_phone)

            if extract_domain:
                df = extract_email_domain(df)  # Ensure 'Domain' column is created

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

            # Apply OpenAI prompt custom transformation
            if custom_request:
                df = generate_openai_response_and_apply(custom_request, df)

            # Display the cleaned data
            st.write("### Data Preview (After Cleanup):")
            st.dataframe(df.head())

            # Output format handling
            if output_format == 'CSV':
                file_name = f"{custom_file_name}.csv"
                st.download_button(label="Download CSV", data=df.to_csv(index=False), file_name=file_name, mime="text/csv")
            elif output_format == 'Excel':
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df.to_excel(writer, index=False)
                writer.save()
                st.download_button(label="Download Excel", data=output.getvalue(), file_name=f"{custom_file_name}.xlsx", mime="application/vnd.ms-excel")
            elif output_format == 'TXT':
                st.download_button(label="Download TXT", data=df.to_csv(index=False, sep="\t"), file_name=f"{custom_file_name}.txt", mime="text/plain")
