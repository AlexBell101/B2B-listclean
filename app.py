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

# File uploader and initial DataFrame
uploaded_file = st.file_uploader("Upload your file", type=['csv', 'xls', 'xlsx', 'txt'])

# Check if the file is uploaded and read it
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file, delimiter="\t")

    st.write("### Data Preview (Before Cleanup):")
    st.dataframe(df.head())

# Sidebar options only if the file is uploaded
if 'df' in locals() and not df.empty:
    st.sidebar.title("Cleanup Options")

    # Column Operations
    with st.sidebar.expander("Column Operations"):
        columns_to_combine = st.multiselect("Select columns to combine", df.columns)
        delimiter = st.text_input("Enter a delimiter", value=", ")
        new_column_name = st.text_input("New Combined Column Name", value="Combined Column")
        retain_headings = st.checkbox("Retain original column headings?")
        remove_original = st.checkbox("Remove original columns?")

        columns_to_rename = st.multiselect("Select columns to rename", df.columns)
        new_names = {col: st.text_input(f"New name for '{col}'", value=col) for col in columns_to_rename}

    # Data Cleanup
    with st.sidebar.expander("Data Cleanup"):
        phone_cleanup = st.checkbox("Standardize phone numbers?")
        normalize_names = st.checkbox("Capitalize first letter of names?")
        extract_domain = st.checkbox("Extract email domain?")
        classify_emails = st.checkbox("Classify emails as Personal or Business?")
        remove_personal = st.checkbox("Remove rows with Personal emails?")
        clean_address = st.checkbox("Clean up and separate Address fields?")
        split_city_state_option = st.checkbox("Split combined City and State fields?")
        country_format = st.selectbox("Country field format", ["Leave As-Is", "Long Form", "Country Code"])

        # Checkbox for splitting full name and conditionally displaying the dropdown
        split_name_option = st.checkbox("Split Full Name into First and Last Name?")
        full_name_column = None
        if split_name_option:
            full_name_column = st.selectbox("Select Full Name column to split", df.columns)

    # Custom Fields
    with st.sidebar.expander("Custom Fields"):
        add_lead_source = st.checkbox("Add 'Lead Source' field?")
        lead_source_value = st.text_input("Lead Source Value") if add_lead_source else None
        add_lead_source_detail = st.checkbox("Add 'Lead Source Detail' field?")
        lead_source_detail_value = st.text_input("Lead Source Detail Value") if add_lead_source_detail else None
        add_campaign = st.checkbox("Add 'Campaign' field?")
        campaign_value = st.text_input("Campaign Value") if add_campaign else None

    # Advanced Transformations (Karmic AI Prompt)
    with st.sidebar.expander("Advanced Transformations"):
        custom_request = st.text_area("Karmic AI Prompt")

    # Custom File Name and Output Format
    custom_file_name = st.sidebar.text_input("Custom File Name (without extension)", value="cleaned_data")
    output_format = st.sidebar.selectbox("Select output format", ['CSV', 'Excel', 'TXT'])

    # Clean the data and apply transformations
    if st.button("Enlighten your data"):
        # Apply all the cleanup functions (e.g., capitalizing names, phone cleanup, etc.)
        if normalize_names and 'Name' in df.columns:
            df = capitalize_names(df)

        if split_name_option and full_name_column and full_name_column in df.columns:
            df = split_first_last_name(df, full_name_column)

        if 'Country' in df.columns:
            df = convert_country(df, country_format)

        if phone_cleanup and 'Phone' in df.columns:
            df['Phone'] = df['Phone'].apply(clean_phone)

        if extract_domain:
            df = extract_email_domain(df)

        if classify_emails:
            df = classify_email_type(df, personal_domains)

        if remove_personal:
            df = remove_personal_emails(df, personal_domains)

        if clean_address:
            df = split_full_address(df)  # Replaces both split_address_2 and split_city_state

        if columns_to_combine:
            df = combine_columns(df, columns_to_combine, delimiter, new_column_name, retain_headings, remove_original)

        if columns_to_rename:
            df = rename_columns(df, new_names)

        if add_lead_source:
            df['Lead Source'] = lead_source_value
        if add_lead_source_detail:
            df['Lead Source Detail'] = lead_source_detail_value
        if add_campaign:
            df['Campaign'] = campaign_value

        if custom_request:
            df = generate_openai_response_and_apply(custom_request, df)

        # Show the cleaned data preview
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
else:
    st.write("Please upload a file to proceed.")
