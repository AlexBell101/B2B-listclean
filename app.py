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
client.api_key = st.secrets["OPENAI_API_KEY"]

# List of common personal email domains
personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'outlook.com']

# Initialize df as None at the start
df = None  # This ensures df is defined before we reference it

# Helper functions
def country_to_code(country_name):
    """
    Converts a country name to its respective ISO Alpha-2 country code.
    Arguments:
    - country_name: str : Full name of the country to be converted.
    Returns:
    - str : ISO Alpha-2 code of the country or the original country name if not found.
    """
    try:
        return pycountry.countries.lookup(country_name).alpha_2
    except LookupError:
        return country_name

def code_to_country(country_code):
    """
    Converts a country code to its respective full country name.
    Arguments:
    - country_code: str : ISO Alpha-2 country code.
    Returns:
    - str : Full country name or the original country code if not found.
    """
    try:
        return pycountry.countries.get(alpha_2=country_code).name
    except LookupError:
        return country_code

def convert_country(df, format_type="Long Form"):
    """
    Converts the country format for the 'Country' column in the DataFrame.
    Arguments:
    - df: DataFrame : The dataframe containing country information.
    - format_type: str : Desired format, either "Long Form" or "Country Code".
    Returns:
    - DataFrame : Updated dataframe with modified 'Country' column.
    """
    if 'Country' in df.columns:
        if format_type == "Country Code":
            df['Country'] = df['Country'].apply(lambda x: country_to_code(x) if pd.notnull(x) else x)
        elif format_type == "Long Form":
            df['Country'] = df['Country'].apply(lambda x: code_to_country(country_to_code(x)) if pd.notnull(x) else x)
    return df

def clean_phone(phone):
    """
    Standardizes a phone number to the E.164 format.
    Arguments:
    - phone: str : Phone number to be standardized.
    Returns:
    - str : Standardized phone number or the original input if parsing fails.
    """
    try:
        parsed_phone = phonenumbers.parse(phone, "US")
        return phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return phone

def extract_email_domain(df):
    """
    Extracts the domain from email addresses in the 'Email' column.
    Arguments:
    - df: DataFrame : The dataframe containing the 'Email' column.
    Returns:
    - DataFrame : Updated dataframe with a new 'Domain' column.
    """
    if 'Email' in df.columns:
        df['Domain'] = df['Email'].apply(lambda x: x.split('@')[1] if isinstance(x, str) and '@' in x else '')
    else:
        st.error("'Email' column not found in the dataframe")
    return df

def classify_email_type(df, personal_domains):
    """
    Classifies email addresses in the 'Domain' column as either 'Personal' or 'Business'.
    Arguments:
    - df: DataFrame : The dataframe containing the 'Domain' column.
    - personal_domains: list : A list of common personal email domains.
    Returns:
    - DataFrame : Updated dataframe with a new 'Email Type' column.
    """
    if 'Domain' in df.columns:
        df['Email Type'] = df['Domain'].apply(lambda domain: 'Personal' if domain in personal_domains else 'Business')
    return df

def remove_personal_emails(df, personal_domains):
    """
    Removes rows containing personal email domains from the dataframe.
    Arguments:
    - df: DataFrame : The dataframe containing the 'Domain' column.
    - personal_domains: list : A list of common personal email domains.
    Returns:
    - DataFrame : Updated dataframe without rows that have personal email domains.
    """
    return df[df['Domain'].apply(lambda domain: domain not in personal_domains)]

def split_full_address(df):
    """
    Splits the 'Address' column into separate columns: Street, City, State, PostalCode, and Country.
    Arguments:
    - df: DataFrame : The dataframe containing the 'Address' column.
    Returns:
    - DataFrame : Updated dataframe with separated address components and original 'Address' column dropped.
    """
    if 'Address' in df.columns:
        def extract_components(address):
            street, city, state, postal_code, country = '', '', '', '', ''

            if pd.notnull(address):
                country_match = re.search(r'\b(?:United Kingdom|UK|United States)\b', address, re.IGNORECASE)
                if country_match:
                    country = country_match.group(0)
                    if country.upper() == "UK":
                        country = "United Kingdom"  # Normalize UK to United Kingdom
                    address = address.replace(country, '').strip()
                else:
                    country = "United States"

                if country == 'United Kingdom':
                    postal_match = re.search(r'[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}', address)
                    if postal_match:
                        postal_code = postal_match.group(0)
                        address = address.replace(postal_code, '').strip()

                    if ',' in address:
                        parts = address.split(',')
                        street = parts[0].strip()
                        city = parts[1].strip() if len(parts) > 1 else ''
                    else:
                        street = address.strip()

                elif country == 'United States':
                    postal_match = re.search(r'\d{5}(?:-\d{4})?', address)
                    if postal_match:
                        postal_code = postal_match.group(0)
                        address = address.replace(postal_code, '').strip()

                    state_match = re.search(r'\b[A-Z]{2}\b', address)
                    if state_match:
                        state = state_match.group(0)
                        address = address.replace(state, '').strip()

                    if ',' in address:
                        parts = address.split(',')
                        street = parts[0].strip()
                        city = parts[1].strip() if len(parts) > 1 else ''
                    else:
                        street = address.strip()

            return {'Street': street, 'City': city, 'State': state, 'PostalCode': postal_code, 'Country': country}

        address_components = df['Address'].apply(extract_components)
        df = pd.concat([df, pd.DataFrame(address_components.tolist())], axis=1)

    df.drop(columns=['Address'], inplace=True)
    return df

def split_city_state(df):
    """
    Splits the 'City_State' column into separate 'City' and 'State' columns.
    Arguments:
    - df: DataFrame : The dataframe containing the 'City_State' column.
    Returns:
    - DataFrame : Updated dataframe with separated 'City' and 'State' columns.
    """
    if 'City_State' in df.columns:
        df[['City', 'State']] = df['City_State'].str.split(',', 1, expand=True)
        df['City'] = df['City'].str.strip()
        df['State'] = df['State'].str.strip()
    return df

def combine_columns(df, columns_to_combine, delimiter, new_column_name, retain_headings, remove_original):
    """
    Combines multiple columns into a new single column.
    Arguments:
    - df: DataFrame : The dataframe containing the columns to be combined.
    - columns_to_combine: list : The list of columns to be combined.
    - delimiter: str : The string to separate each column's content.
    - new_column_name: str : Name for the new combined column.
    - retain_headings: bool : Whether to include column names in the combined column content.
    - remove_original: bool : Whether to remove the original columns after combination.
    Returns:
    - DataFrame : Updated dataframe with combined columns.
    """
    if columns_to_combine:
        if retain_headings:
            df[new_column_name] = df[columns_to_combine].astype(str).apply(
                lambda row: delimiter.join([f"{col}: {value}" for col, value in zip(columns_to_combine, row.values)]),
                axis=1
            )
        else:
            df[new_column_name] = df[columns_to_combine].astype(str).apply(
                lambda row: delimiter.join(row.values), axis=1)
        if remove_original:
            df = df.drop(columns=columns_to_combine)
        st.success(f"Columns {', '.join(columns_to_combine)} have been combined into '{new_column_name}'")
    return df

def rename_columns(df, new_names):
    """
    Renames columns in the dataframe.
    Arguments:
    - df: DataFrame : The dataframe containing the columns to be renamed.
    - new_names: dict : A dictionary of old column names to new column names.
    Returns:
    - DataFrame : Updated dataframe with renamed columns.
    """
    if new_names:
        existing_columns = [col for col in new_names.keys() if col in df.columns]
        if existing_columns:
            df = df.rename(columns={col: new_names[col] for col in existing_columns})
            st.success(f"Columns renamed: {new_names}")
        else:
            st.warning("No valid columns selected for renaming.")
    else:
        st.warning("Please provide new names for the selected columns.")
    return df

def capitalize_names(df):
    """
    Capitalizes the first letter of each word in the 'Name' column.
    Arguments:
    - df: DataFrame : The dataframe containing the 'Name' column.
    Returns:
    - DataFrame : Updated dataframe with modified 'Name' column.
    """
    if 'Name' in df.columns:
        df['Name'] = df['Name'].str.title()
        st.success("Capitalized the first letter of each word in the 'Name' column")
    else:
        st.error("'Name' column not found in the dataframe")
    return df

def split_first_last_name(df, full_name_column):
    """
    Splits a full name into 'First Name' and 'Last Name' columns.
    Arguments:
    - df: DataFrame : The dataframe containing the full name column.
    - full_name_column: str : The name of the column containing the full name.
    Returns:
    - DataFrame : Updated dataframe with separate 'First Name' and 'Last Name' columns.
    """
    if full_name_column in df.columns:
        df['First Name'] = df[full_name_column].apply(lambda x: x.split()[0] if isinstance(x, str) else "")
        df['Last Name'] = df[full_name_column].apply(lambda x: " ".join(x.split()[1:]) if isinstance(x, str) else "")
        st.success(f"Column '{full_name_column}' has been split into 'First Name' and 'Last Name'")
    else:
        st.error(f"'{full_name_column}' not found in columns")
    return df

def extract_python_code(response_text):
    """
    Extracts the Python code from a response text containing markdown-style code blocks.
    Arguments:
    - response_text: str : The response text from OpenAI.
    Returns:
    - str : Extracted Python code.
    """
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

def clean_and_validate_code(python_code):
    """
    Cleans and validates Python code to ensure proper use of the dataframe 'df'.
    Arguments:
    - python_code: str : The Python code to be cleaned.
    Returns:
    - str : Cleaned Python code.
    """
    python_code = python_code.replace("data", "df")
    if 'df' in python_code and 'import' not in python_code:
        return python_code
    return None

def detect_relevant_column(df, prompt):
    """
    Automatically detects the most relevant column based on keywords in the prompt.
    If no relevant column is found, prompt the user to specify a column.
    Arguments:
    - df: DataFrame : The dataframe to analyze.
    - prompt: str : The user's prompt to determine context.
    Returns:
    - str : The name of the relevant column if found, otherwise None.
    """
    prompt_keywords = {
        'name': ['name', 'first', 'last'],
        'phone': ['phone', 'mobile'],
        'email': ['email', 'mail'],
        'address': ['address', 'city', 'state', 'country'],
        'domain': ['domain', 'website'],
        'title': ['title', 'job', 'role', 'position']
    }

    for column in df.columns:
        column_lower = column.lower()
        for key, keywords in prompt_keywords.items():
            if any(keyword in prompt.lower() for keyword in keywords):
                if key in column_lower:
                    return column
    return None

def generate_openai_response_and_apply(prompt, df):
    """
    Generates Python code using OpenAI based on a user prompt and applies it to the dataframe.
    Arguments:
    - prompt: str : The user's request for transformation.
    - df: DataFrame : The dataframe to be modified.
    Returns:
    - DataFrame : Updated dataframe after applying the generated transformation.
    """
    try:
        # Detect the relevant column automatically
        relevant_column = detect_relevant_column(df, prompt)

        if not relevant_column:
            st.error("No relevant column found in the prompt. Please specify the column explicitly.")
            return df

        # Refined prompt with the detected column
        refined_prompt = f"""
        Please generate only the Python code that modifies the '{relevant_column}' column of the dataframe `df`.
        Avoid including imports, data definitions, print statements, or any explanations.
        The code should focus exclusively on modifying the `df` dataframe based on the following request:
        {prompt}
        """

        # Send the prompt to OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": refined_prompt}
            ],
            max_tokens=500
        )

        # Extract Python code from the response
        response_text = response.choices[0].message.content
        python_code = extract_python_code(response_text)
        python_code = clean_and_validate_code(python_code)

        if not python_code:
            st.error("Invalid Python code returned by OpenAI.")
            return df

        # Execute the generated code
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
