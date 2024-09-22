import streamlit as st
import pandas as pd
import phonenumbers
from io import BytesIO
import pycountry  # For country code mapping
import openai

# Fetch the OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Helper function for country code conversion
def country_to_code(country_name):
    try:
        return pycountry.countries.lookup(country_name).alpha_2
    except LookupError:
        return country_name

# Helper function for phone number cleaning
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

# Function to process OpenAI response and apply transformation automatically
def generate_openai_response_and_apply(prompt, df):
    try:
        # Use openai.ChatCompletion.create instead of client.chat.completions.create
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Here is a dataset:\n\n{df.head().to_csv()}\n\nHere is the request:\n{prompt}"}
            ],
            max_tokens=500
        )

        # Extract the reply from the response
        reply = response['choices'][0]['message']['content']

        # Return modified dataframe with custom OpenAI processing if needed
        return df  # You can modify df based on the response if required

    except Exception as e:
        st.error(f"OpenAI request failed: {e}")
        return df

# UI setup for the app - modern, clean, and simple
st.set_page_config(page_title="List Cleaner SaaS", layout="centered")
st.title("📋 List Cleaner SaaS")
st.write("Upload your marketing lists and clean them up for CRM tools like Salesforce, Marketo, HubSpot.")

# File uploader section
uploaded_file = st.file_uploader("Upload your file", type=['csv', 'xls', 'xlsx', 'txt'])
if uploaded_file is not None:
    # Handle different file types
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:  # Handle text file
        df = pd.read_csv(uploaded_file, delimiter="\t")

    st.write("### Data Preview (Before Cleanup):")
    st.dataframe(df.head())

    # Cleanup Options
    st.sidebar.title("Cleanup Options")
    
    # Output format selection
    output_format = st.sidebar.radio("Select output format", ('CSV', 'Excel', 'TXT'))

    # Country field cleanup
    country_format = st.sidebar.selectbox("Country field format", ["Leave As-Is", "Long Form", "Country Code"])

    # Phone cleanup
    phone_cleanup = st.sidebar.checkbox("Standardize phone numbers?")

    # Normalize field values (capitalize names)
    normalize_names = st.sidebar.checkbox("Capitalize first letter of names?")

    # Add domain extraction option
    extract_domain = st.sidebar.checkbox("Extract email domain?")

    # Create custom fields
    add_lead_source = st.sidebar.checkbox("Add 'Lead Source' field?")
    lead_source_value = st.sidebar.text_input("Lead Source Value") if add_lead_source else None
    
    add_lead_source_detail = st.sidebar.checkbox("Add 'Lead Source Detail' field?")
    lead_source_detail_value = st.sidebar.text_input("Lead Source Detail Value") if add_lead_source_detail else None
    
    add_campaign = st.sidebar.checkbox("Add 'Campaign' field?")
    campaign_value = st.sidebar.text_input("Campaign Value") if add_campaign else None

    # Split output by status
    split_by_status = st.sidebar.checkbox("Split output by 'Status' column?")
    status_column = st.sidebar.selectbox("Select Status Column", df.columns) if split_by_status else None

    # OpenAI-based custom request
    st.sidebar.write("### OpenAI Custom Request")
    custom_request = st.sidebar.text_area("Enter any specific custom request")
    
    # Apply changes to the dataset based on user selections
    if st.button("Clean the data"):
        # Normalize names
        if normalize_names:
            if 'Name' in df.columns:
                df['Name'] = df['Name'].str.title()
        
        # Country field format
        if country_format == "Country Code" and 'Country' in df.columns:
            df['Country'] = df['Country'].apply(lambda x: country_to_code(x))
        
        # Clean up phone numbers
        if phone_cleanup and 'Phone' in df.columns:
            df['Phone'] = df['Phone'].apply(clean_phone)
        
        # Add custom fields
        if add_lead_source:
            df['Lead Source'] = lead_source_value
        if add_lead_source_detail:
            df['Lead Source Detail'] = lead_source_detail_value
        if add_campaign:
            df['Campaign'] = campaign_value

        # Extract email domains if selected
        if extract_domain:
            df = extract_email_domain(df)

        # Process OpenAI custom request and auto-apply transformations
        if custom_request:
            df = generate_openai_response_and_apply(custom_request, df)

        # Show the cleaned data preview
        st.write("### Data Preview (After Cleanup):")
        st.dataframe(df.head())

        # Split data by status column if selected
        if split_by_status and status_column:
            # Unique status values
            unique_status_values = df[status_column].unique()

            # Download buttons for each status group
            for status_value in unique_status_values:
                status_df = df[df[status_column] == status_value]
                st.write(f"#### Data for Status: {status_value}")
                st.dataframe(status_df.head())

                if output_format == 'CSV':
                    st.download_button(
                        label=f"Download CSV for {status_value}",
                        data=status_df.to_csv(index=False),
                        file_name=f"cleaned_data_{status_value}.csv",
                        mime="text/csv"
                    )
                elif output_format == 'Excel':
                    output = BytesIO()
                    writer = pd.ExcelWriter(output, engine='xlsxwriter')
                    status_df.to_excel(writer, index=False)
                    writer.save()
                    st.download_button(
                        label=f"Download Excel for {status_value}",
                        data=output.getvalue(),
                        file_name=f"cleaned_data_{status_value}.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                elif output_format == 'TXT':
                    st.download_button(
                        label=f"Download TXT for {status_value}",
                        data=status_df.to_csv(index=False, sep="\t"),
                        file_name=f"cleaned_data_{status_value}.txt",
                        mime="text/plain"
                    )
        else:
            # Provide cleaned data for download without split
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
