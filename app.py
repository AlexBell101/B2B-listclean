import openai
import streamlit as st
import pandas as pd
import phonenumbers
from io import BytesIO
import pycountry
import re

# Ensure this function is defined before calling it
def extract_python_code(response_text):
    code_block = re.search(r'```(.*?)```', response_text, re.DOTALL)
    if code_block:
        code = code_block.group(1).strip()
        if code.startswith("python"):
            code = code[len("python"):].strip()
        code = re.sub(r'import.*', '', code)
        code = re.sub(r'data\s*=.*', '', code)
        code = re.sub(r'print\(.*\)', '', code)
        open_braces = code.count('{')
        close_braces = code.count('}')
        if open_braces != close_braces:
            code = re.sub(r'[{}]', '', code)
        code_lines = code.split('\n')
        code = "\n".join(line.lstrip() for line in code_lines)
        return code
    else:
        return response_text.strip()
        
# Set the page config before any other Streamlit code
st.set_page_config(page_title="List Karma", layout="centered")

# Custom CSS to style the sidebar and select boxes
st.markdown(
    """
    <style>

    /* Change the font color and style of sidebar components */
    [data-testid="stSidebar"] * {
        color: white;
        font-family: 'Roboto', sans-serif;
    }

    /* Set font to Roboto for the entire app */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# Create a custom OpenAI API client
client = openai

# Fetch the OpenAI API key from Streamlit secrets
client.api_key = st.secrets["OPENAI_API_KEY"]

# List of common personal email domains
personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'outlook.com']

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

# Function to classify email type as 'Personal' or 'Business'
def classify_email_type(df):
    if 'Email' in df.columns:
        df['Email Type'] = df['Domain'].apply(lambda domain: 'Personal' if domain in personal_domains else 'Business')
    return df

# Function to remove rows with personal emails
def remove_personal_emails(df):
    return df[df['Domain'].apply(lambda domain: domain not in personal_domains)]

# Function to separate Address 2 from Address 1
def split_address_2(df):
    if 'Address' in df.columns:
        df['Address 1'] = df['Address'].apply(lambda x: re.split(r'(?i)\b(Apt|Unit|Suite)\b', x)[0].strip())
        df['Address 2'] = df['Address'].apply(lambda x: re.search(r'(?i)(Apt|Unit|Suite).*', x).group(0) if re.search(r'(?i)(Apt|Unit|Suite).*', x) else "")
    return df

# Function to split city and state if they are combined
def split_city_state(df):
    if 'City_State' in df.columns:
        df[['City', 'State']] = df['City_State'].str.split(',', 1, expand=True)
        df['City'] = df['City'].str.strip()
        df['State'] = df['State'].str.strip()
    return df

# Function to generate and apply OpenAI response
def generate_openai_response_and_apply(prompt, df):
    try:
        refined_prompt = f"""
        Please generate Python code that modifies the dataframe `df`.
        The dataframe has the following columns: {', '.join(df.columns)}.
        Focus only on modifying the dataframe based on this request: {prompt}.
        Avoid adding imports, data definitions, or print statements.
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": refined_prompt}
            ],
            max_tokens=500
        )
        response_text = response.choices[0].message.content
        python_code = extract_python_code(response_text)
        python_code = clean_and_validate_code(python_code)
        if not python_code:
            st.error("Invalid Python code returned by OpenAI")
            return df
        local_env = {'df': df}
        try:
            exec(python_code, {}, local_env)
            df = local_env['df']
        except SyntaxError as syntax_error:
            st.error(f"Error executing OpenAI code: {syntax_error}")
            return df
        return df
    except Exception as e:
        st.error(f"OpenAI request failed: {e}")
        return df

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
