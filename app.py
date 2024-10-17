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

# UI setup for the app with tooltips
st.title("📋 List Karma")
st.write("Upload your marketing lists and clean them up for CRM tools like Salesforce, Marketo, HubSpot. Use the Karmic AI Prompt if you need a specific transformation applied to your file.")
st.markdown("""<small><i>Use this tool to streamline and prepare your marketing list data for downstream tools.</i></small>""", unsafe_allow_html=True)

# Create a custom OpenAI API client
client = openai
client.api_key = st.secrets["OPENAI_API_KEY"]

# List of common personal email domains
personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'outlook.com']

# Initialize df as None at the start
df = None  # This ensures df is defined before we reference it

# Helper functions with added tooltips
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
    """Convert country information from full name to code or vice versa."""
    if 'Country' in df.columns:
        if format_type == "Country Code":
            df['Country'] = df['Country'].apply(lambda x: country_to_code(x) if pd.notnull(x) else x)
        elif format_type == "Long Form":
            df['Country'] = df['Country'].apply(lambda x: code_to_country(country_to_code(x)) if pd.notnull(x) else x)
    return df

def clean_phone(phone):
    """Clean phone numbers to E164 format."""
    try:
        parsed_phone = phonenumbers.parse(phone, "US")
        return phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return phone

def extract_email_domain(df):
    """Extract the domain from email addresses."""
    if 'Email' in df.columns:
        df['Domain'] = df['Email'].apply(lambda x: x.split('@')[1] if isinstance(x, str) and '@' in x else '')
    else:
        st.error("'Email' column not found in the dataframe")
    return df

def classify_email_type(df, personal_domains):
    """Classify email as Personal or Business based on domain."""
    if 'Domain' in df.columns:
        df['Email Type'] = df['Domain'].apply(lambda domain: 'Personal' if domain in personal_domains else 'Business')
    return df

def remove_personal_emails(df, personal_domains):
    """Remove rows with personal email addresses."""
    return df[df['Domain'].apply(lambda domain: domain not in personal_domains)]

def split_full_address(df):
    """Split full addresses into individual components (street, city, state, postal code, country)."""
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
    """Split the 'City_State' column into separate 'City' and 'State' columns."""
    if 'City_State' in df.columns:
        df[['City', 'State']] = df['City_State'].str.split(',', 1, expand=True)
        df['City'] = df['City'].str.strip()
        df['State'] = df['State'].str.strip()
    return df

def capitalize_names(df):
    """Capitalize the first letter of each word in the 'Name' column."""
    if 'Name' in df.columns:
        df['Name'] = df['Name'].str.title()
        st.success("Capitalized the first letter of each word in the 'Name' column")
    else:
        st.error("'Name' column not found in the dataframe")
    return df

def split_first_last_name(df, full_name_column):
    """Split full name into 'First Name' and 'Last Name'."""
    if full_name_column in df.columns:
        df['First Name'] = df[full_name_column].apply(lambda x: x.split()[0] if isinstance(x, str) else "")
        df['Last Name'] = df[full_name_column].apply(lambda x: " ".join(x.split()[1:]) if isinstance(x, str) else "")
        st.success(f"Column '{full_name_column}' has been split into 'First Name' and 'Last Name'")
    else:
        st.error(f"'{full_name_column}' not found in columns")
    return df

def rename_columns(df, new_names):
    """Rename columns based on user-provided mappings."""
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

# File uploader and initial DataFrame
uploaded_file = st.file_uploader("Upload your file", type=['csv', 'xls', 'xlsx', 'txt'], help="Upload a CSV, Excel, or TXT file containing your marketing data.")

# Check if the file is uploaded and read it
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file, delimiter="\t")

    st.write("### Data Preview (Before Cleanup):")
    st.dataframe(df.head(), help="This is a preview of your uploaded data before any transformations are applied.")

# Sidebar options only if the file is uploaded
if df is not None and not df.empty:
    st.sidebar.title("Cleanup Options", help="Select various options to clean and modify your marketing data.")

    # Column Operations
    with st.sidebar.expander("Column Operations", expanded=True):
        columns_to_combine = st.multiselect("Select columns to combine", df.columns, help="Select multiple columns to combine them into one.")
        delimiter = st.text_input("Enter a delimiter", value=", ", help="Specify a delimiter to use when combining columns.")
        new_column_name = st.text_input("New Combined Column Name", value="Combined Column", help="Provide a name for the new combined column.")
        retain_headings = st.checkbox("Retain original column headings?", help="Keep the original column headings in the combined output.")
        remove_original = st.checkbox("Remove original columns?", help="Remove the columns that were combined.")

    # Rename Columns (Separate Functionality)
    with st.sidebar.expander("Rename Columns", expanded=True):
        columns_to_rename = st.multiselect("Select columns to rename", df.columns, help="Select columns that you want to rename.")
        new_names = {col: st.text_input(f"New name for '{col}'", value=col, help="Provide a new name for the selected column.") for col in columns_to_rename}

    # Data Cleanup
    with st.sidebar.expander("Data Cleanup", expanded=True):
        phone_cleanup = st.checkbox("Standardize phone numbers?", help="Format phone numbers to a standard E.164 format.")
        normalize_names = st.checkbox("Capitalize first letter of names?", help="Capitalize the first letter of each word in the 'Name' column.")
        extract_domain = st.checkbox("Extract email domain?", help="Extract the domain from email addresses, e.g., 'example.com'.")
        classify_emails = st.checkbox("Classify emails as Personal or Business?", help="Classify email addresses based on whether they are personal or business.")
        remove_personal = st.checkbox("Remove rows with Personal emails?", help="Remove rows containing personal email addresses like Gmail or Yahoo.")
        clean_address = st.checkbox("Clean up and separate Address fields?", help="Split full addresses into individual components like street, city, etc.")
        split_city_state_option = st.checkbox("Split combined City and State fields?", help="Split the 'City_State' column into separate 'City' and 'State' columns.")
        country_format = st.selectbox("Country field format", ["Leave As-Is", "Long Form", "Country Code"], help="Choose the desired format for the country field.")

        # Checkbox for splitting full name and conditionally displaying the dropdown
        split_name_option = st.checkbox("Split Full Name into First and Last Name?", help="Split a full name into separate 'First Name' and 'Last Name' columns.")
        full_name_column = None
        if split_name_option:
            full_name_column = st.selectbox("Select Full Name column to split", df.columns, help="Select the column that contains full names to split.")

    # Custom Fields
    with st.sidebar.expander("Custom Fields", expanded=True):
        add_lead_source = st.checkbox("Add 'Lead Source' field?", help="Add a 'Lead Source' field to your dataset.")
        lead_source_value = st.text_input("Lead Source Value", help="Provide a value for the 'Lead Source' field.") if add_lead_source else None
        add_lead_source_detail = st.checkbox("Add 'Lead Source Detail' field?", help="Add a 'Lead Source Detail' field to your dataset.")
        lead_source_detail_value = st.text_input("Lead Source Detail Value", help="Provide a value for the 'Lead Source Detail' field.") if add_lead_source_detail else None
        add_campaign = st.checkbox("Add 'Campaign' field?", help="Add a 'Campaign' field to your dataset.")
        campaign_value = st.text_input("Campaign Value", help="Provide a value for the 'Campaign' field.") if add_campaign else None

    # Advanced Transformations (Karmic AI Prompt)
    with st.sidebar.expander("Advanced Transformations", expanded=True):
        custom_request = st.text_area("Karmic AI Prompt", help="Use this field to input a custom request for AI-based transformations on your data.")

    # Custom File Name and Output Format
    custom_file_name = st.sidebar.text_input("Custom File Name (without extension)", value="cleaned_data", help="Specify a name for the cleaned data file.")
    output_format = st.sidebar.selectbox("Select output format", ['CSV', 'Excel', 'TXT'], help="Choose the format in which you'd like to download the cleaned data.")

    # Clean the data and apply transformations
    if st.button("Enlighten your data", help="Click to apply all selected transformations to your data."):
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

        if split_city_state_option:
            df = split_city_state(df)

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
        st.dataframe(df.head(), help="This is a preview of your data after all selected transformations have been applied.")

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
