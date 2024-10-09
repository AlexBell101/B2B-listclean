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
    try:
        return pycountry.countries.lookup(country_name).alpha_2
    except LookupError:
        return country_name

def code_to_country(country_code):
    try:
        return pycountry.countries.get(alpha_2=country_code).name
    except LookupError:
        return country_code

def convert_country(df, format_type="Long Form"):
    if 'Country' in df.columns:
        if format_type == "Country Code":
            df['Country'] = df['Country'].apply(lambda x: country_to_code(x) if pd.notnull(x) else x)
        elif format_type == "Long Form":
            df['Country'] = df['Country'].apply(lambda x: code_to_country(country_to_code(x)) if pd.notnull(x) else x)
    return df

def clean_phone(phone):
    try:
        parsed_phone = phonenumbers.parse(phone, "US")
        return phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return phone

def extract_email_domain(df):
    if 'Email' in df.columns:
        df['Domain'] = df['Email'].apply(lambda x: x.split('@')[1] if isinstance(x, str) and '@' in x else '')
    else:
        st.error("'Email' column not found in the dataframe")
    return df

def classify_email_type(df, personal_domains):
    if 'Domain' in df.columns:
        df['Email Type'] = df['Domain'].apply(lambda domain: 'Personal' if domain in personal_domains else 'Business')
    return df

def remove_personal_emails(df, personal_domains):
    return df[df['Domain'].apply(lambda domain: domain not in personal_domains)]

def split_full_address(df):
    if 'Address' in df.columns:
        def extract_components(address):
            # Initial empty values
            street, city, state, postal_code, country = '', '', '', '', ''

            if pd.notnull(address):
                # Extract postal code (US ZIP format or alphanumeric for international)
                postal_match = re.search(r'(\d{5}(?:-\d{4})?|\b[A-Z\d]{3,10}\b)', address)
                if postal_match:
                    postal_code = postal_match.group(0)
                    address = address.replace(postal_code, '').strip()

                # Extract state (2-letter code or full state name)
                state_match = re.search(r'\b[A-Z]{2}\b', address)
                if state_match:
                    state = state_match.group(0)
                    address = address.replace(state, '').strip()

                # Attempt to extract country (common country names)
                country_match = re.search(r'\b(?:United States|Canada|United Kingdom|Australia)\b', address, re.IGNORECASE)
                if country_match:
                    country = country_match.group(0)
                    address = address.replace(country, '').strip()

                # The remaining part is the street and city, split at the last comma
                if ',' in address:
                    parts = address.rsplit(',', 1)
                    street = parts[0].strip()  # Everything before the last comma is street
                    city = parts[1].strip().rstrip(',')  # Remove trailing comma from city
                else:
                    street = address.strip()  # Fallback for no commas

            return {'Street': street, 'City': city, 'State': state, 'PostalCode': postal_code, 'Country': country}

        # Apply the component extraction function
        address_components = df['Address'].apply(extract_components)
        df = pd.concat([df, pd.DataFrame(address_components.tolist())], axis=1)

    # Remove the original 'Address' column
    df.drop(columns=['Address'], inplace=True)
    
    return df

def split_city_state(df):
    if 'City_State' in df.columns:
        df[['City', 'State']] = df['City_State'].str.split(',', 1, expand=True)
        df['City'] = df['City'].str.strip()
        df['State'] = df['State'].str.strip()
    return df

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
        if remove_original:
            df = df.drop(columns=columns_to_combine)
        st.success(f"Columns {', '.join(columns_to_combine)} have been combined into '{new_column_name}'")
    return df

def rename_columns(df, new_names):
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
    if 'Name' in df.columns:
        df['Name'] = df['Name'].str.title()
        st.success("Capitalized the first letter of each word in the 'Name' column")
    else:
        st.error("'Name' column not found in the dataframe")
    return df

def split_first_last_name(df, full_name_column):
    if full_name_column in df.columns:
        df['First Name'] = df[full_name_column].apply(lambda x: x.split()[0] if isinstance(x, str) else "")
        df['Last Name'] = df[full_name_column].apply(lambda x: " ".join(x.split()[1:]) if isinstance(x, str) else "")
        st.success(f"Column '{full_name_column}' has been split into 'First Name' and 'Last Name'")
    else:
        st.error(f"'{full_name_column}' not found in columns")
    return df

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
if df is not None and not df.empty:
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
