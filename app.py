import openai
import streamlit as st
import pandas as pd
import phonenumbers
from io import BytesIO
import pycountry
import re  # Import the regex module

# Create a custom OpenAI API client
client = openai

# Fetch the OpenAI API key from Streamlit secrets
client.api_key = st.secrets["OPENAI_API_KEY"]

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

# Fetch the OpenAI API key from Streamlit secrets
client.api_key = st.secrets["OPENAI_API_KEY"]

# Function to extract Python code from OpenAI's response and remove 'python' prefix
def extract_python_code(response_text):
    # Use regex to extract Python code between ``` markers or similar
    code_block = re.search(r'```(.*?)```', response_text, re.DOTALL)
    if code_block:
        code = code_block.group(1).strip()
        # Remove any 'python' prefix from the code block
        if code.startswith("python"):
            code = code[len("python"):].strip()
        return code
    else:
        # If no ``` block, return the whole response
        return response_text.strip()

# Function to validate the Python code before execution
def validate_python_code(python_code):
    # Ensure the code references 'df' and does not contain problematic statements
    if 'df' in python_code and 'import' not in python_code:
        return True
    return False

# Now, use client.chat.completions.create()
def generate_openai_response_and_apply(prompt, df):
    try:
        # Make the OpenAI API request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Here is a dataset:\n\n{df.head().to_csv()}\n\nHere is the request:\n{prompt}\nPlease return only valid Python code without explanations."}
            ],
            max_tokens=500
        )

        # Extract Python code from the response
        response_text = response.choices[0].message.content
        python_code = extract_python_code(response_text)

        # Display OpenAI generated code for debugging
        st.write("**OpenAI Suggested Code:**")
        st.code(python_code)

        # Validate the Python code
        if not validate_python_code(python_code):
            st.error("Invalid Python code returned by OpenAI")
            return df

        # Execute the extracted code in a controlled local environment
        local_env = {'df': df}
        try:
            exec(python_code, {}, local_env)
            df = local_env['df']  # Extract the updated DataFrame after exec
        except SyntaxError as syntax_error:
            st.error(f"Error executing OpenAI code: {syntax_error}")
            return df

        return df

    except Exception as e:
        st.error(f"OpenAI request failed: {e}")
        return df
# UI setup for the app
st.set_page_config(page_title="List Cleaner SaaS", layout="centered")
st.title("📋 List Cleaner SaaS")
st.write("Upload your marketing lists and clean them up for CRM tools like Salesforce, Marketo, HubSpot.")

# File uploader section
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

    # Sidebar cleanup options
    st.sidebar.title("Cleanup Options")
    output_format = st.sidebar.radio("Select output format", ('CSV', 'Excel', 'TXT'))
    country_format = st.sidebar.selectbox("Country field format", ["Leave As-Is", "Long Form", "Country Code"])
    phone_cleanup = st.sidebar.checkbox("Standardize phone numbers?")
    normalize_names = st.sidebar.checkbox("Capitalize first letter of names?")
    extract_domain = st.sidebar.checkbox("Extract email domain?")

    # Custom fields
    add_lead_source = st.sidebar.checkbox("Add 'Lead Source' field?")
    lead_source_value = st.sidebar.text_input("Lead Source Value") if add_lead_source else None
    
    add_lead_source_detail = st.sidebar.checkbox("Add 'Lead Source Detail' field?")
    lead_source_detail_value = st.sidebar.text_input("Lead Source Detail Value") if add_lead_source_detail else None
    
    add_campaign = st.sidebar.checkbox("Add 'Campaign' field?")
    campaign_value = st.sidebar.text_input("Campaign Value") if add_campaign else None

    # Split output by status
    split_by_status = st.sidebar.checkbox("Split output by 'Status' column?")
    status_column = st.sidebar.selectbox("Select Status Column", df.columns) if split_by_status else None

    # OpenAI custom request
    st.sidebar.write("### OpenAI Custom Request")
    custom_request = st.sidebar.text_area("Enter any specific custom request")

    # Clean the data button
    if st.button("Clean the data"):
        if normalize_names and 'Name' in df.columns:
            df['Name'] = df['Name'].str.title()

        if country_format == "Country Code" and 'Country' in df.columns:
            df['Country'] = df['Country'].apply(lambda x: country_to_code(x))

        if phone_cleanup and 'Phone' in df.columns:
            df['Phone'] = df['Phone'].apply(clean_phone)

        if extract_domain:
            df = extract_email_domain(df)

        if custom_request:
            df = generate_openai_response_and_apply(custom_request, df)

        st.write("### Data Preview (After Cleanup):")
        st.dataframe(df.head())

        if split_by_status and status_column:
            unique_status_values = df[status_column].unique()
            for status_value in unique_status_values:
                status_df = df[df[status_column] == status_value]
                st.write(f"#### Data for Status: {status_value}")
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
