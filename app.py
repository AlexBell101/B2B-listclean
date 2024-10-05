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
            df['Country'] = df['Country'].apply(lambda x: country_to_code(x) if pd.notnull(x) else x)
        elif format_type == "Long Form":
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
def classify_email_type(df, personal_domains):
    if 'Domain' in df.columns:
        df['Email Type'] = df['Domain'].apply(lambda domain: 'Personal' if domain in personal_domains else 'Business')
    return df

# Function to remove rows with personal emails
def remove_personal_emails(df, personal_domains):
    return df[df['Domain'].apply(lambda domain: domain not in personal_domains)]

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
        
# Function to extract and clean Python code from OpenAI's response
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

# Function to validate and replace 'data' with 'df'
def clean_and_validate_code(python_code):
    python_code = python_code.replace("data", "df")
    if 'df' in python_code and 'import' not in python_code:
        return python_code
    return None

def generate_openai_response_and_apply(prompt, df):
    try:
        refined_prompt = f"""
        Please generate only the Python code that modifies the dataframe `df`.
        Avoid including imports, data definitions, print statements, or any explanations.
        The code should focus exclusively on modifying the `df` dataframe based on the following request:
        {prompt}
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
    
    # Sidebar setup with collapsible sections
    st.sidebar.title("Cleanup Options")

    # === NEW: Only show the column operations if `df` is defined ===
    if df is not None:  # Ensure `df` exists

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
   
        # Clean the data and apply transformations
        if st.button("Clean the data"):
            # Normalize names
            if normalize_names and 'Name' in df.columns:
                df['Name'] = df['Name'].str.title()
                
            # Normalize names (capitalize first letter of names)
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

            # Apply combine columns functionality
            if columns_to_combine:
                df = combine_columns(df, columns_to_combine, delimiter, new_column_name, retain_headings, remove_original)

            # Apply rename columns functionality
            if columns_to_rename:
                df = rename_columns(df, new_names)

            # Display the cleaned data
            st.write("### Data Preview (After Cleanup):")
            st.dataframe(df.head())

    # Handle output format and splitting by status
    if split_by_status and status_column:
        unique_status_values = df[status_column].unique()
        for status_value in unique_status_values:
            status_df = df[df[status_column] == status_value]
            st.write(f"#### Data for Status {status_value}")
            st.dataframe(status_df.head())
            
            # Use custom file name and append the correct extension
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
        # Use custom file name for the final download
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
