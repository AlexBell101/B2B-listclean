
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

# Function to convert country name to ISO code or vice versa based on format_type
def convert_country(df, format_type="Long Form"):
    if 'Country' in df.columns:
        if format_type == "Country Code":
            # Convert both full country names and codes to short codes
            df['Country'] = df['Country'].apply(lambda x: country_to_code(x) if pd.notnull(x) else x)
        elif format_type == "Long Form":
            # Convert both short codes and full country names to long form
            df['Country'] = df['Country'].apply(lambda x: code_to_country(country_to_code(x)) if pd.notnull(x) else x)
    return df

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

# Other helper functions go here (e.g., clean_phone, split_address_2, etc.)

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

    # Sidebar options
    st.sidebar.title("Cleanup Options")
    output_format = st.sidebar.radio("Select output format", ('CSV', 'Excel', 'TXT'))
    country_format = st.sidebar.selectbox("Country field format", ["Leave As-Is", "Long Form", "Country Code"])
    phone_cleanup = st.sidebar.checkbox("Standardize phone numbers?")
    normalize_names = st.sidebar.checkbox("Capitalize first letter of names?")
    extract_domain = st.sidebar.checkbox("Extract email domain?")
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

    custom_request = st.sidebar.text_area("Karmic AI Prompt")

    if st.button("Clean the data"):
        if normalize_names and 'Name' in df.columns:
            df['Name'] = df['Name'].str.title()

        # Check if 'Country' column exists before converting it
        if 'Country' in df.columns:
            df = convert_country(df, country_format)  # Apply country conversion based on the selected format

        if phone_cleanup and 'Phone' in df.columns:
            df['Phone'] = df['Phone'].apply(clean_phone)

        if extract_domain or classify_emails or remove_personal:
            df = extract_email_domain(df)  # Ensure 'Domain' column is created

        if clean_address:
            df = split_address_2(df)
        if split_city_state_option:
            df = split_city_state(df)

        if add_lead_source:
            df['Lead Source'] = lead_source_value
        if add_lead_source_detail:
            df['Lead Source Detail'] = lead_source_detail_value
        if add_campaign:
            df['Campaign'] = campaign_value

        if custom_request:
            df = generate_openai_response_and_apply(custom_request, df)

        st.write("### Data Preview (After Cleanup):")
        st.dataframe(df.head())

        if split_by_status and status_column:
            unique_status_values = df[status_column].unique()
            for status_value in unique_status_values:
                status_df = df[df[status_column] == status_value]
                st.write(f"#### Data for Status {status_value}")
                st.dataframe(status_df.head())
                if output_format == 'CSV':
                    st.download_button(label=f"Download CSV for {status_value}",
                                       data=status_df.to_csv(index=False),
                                       file_name=f"cleaned_data_{status_value}.csv",
                                       mime="text/csv")
                elif output_format == 'Excel':
                    output = BytesIO()
                    writer = pd.ExcelWriter(output, engine='xlsxwriter')
                    status_df.to_excel(writer, index=False)
                    writer.save()
                    st.download_button(label=f"Download Excel for {status_value}",
                                       data=output.getvalue(),
                                       file_name=f"cleaned_data_{status_value}.xlsx",
                                       mime="application/vnd.ms-excel")
                elif output_format == 'TXT':
                    st.download_button(label=f"Download TXT for {status_value}",
                                       data=status_df.to_csv(index=False, sep="\t"),
                                       file_name=f"cleaned_data_{status_value}.txt",
                                       mime="text/plain")
        else:
            if output_format == 'CSV':
                st.download_button(label="Download CSV", data=df.to_csv(index=False),
                                   file_name="cleaned_data.csv", mime="text/csv")
            elif output_format == 'Excel':
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df.to_excel(writer, index=False)
                writer.save()
                st.download_button(label="Download Excel", data=output.getvalue(),
                                   file_name="cleaned_data.xlsx", mime="application/vnd.ms-excel")
            elif output_format == 'TXT':
                st.download_button(label="Download TXT", data=df.to_csv(index=False, sep="\t"),
                                   file_name="cleaned_data.txt", mime="text/plain")
