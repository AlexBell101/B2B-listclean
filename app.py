# Function to process OpenAI response and apply transformation automatically
def generate_openai_response_and_apply(prompt, df):
    try:
        # Corrected OpenAI API call with openai.ChatCompletion.create
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

        # Example: Modify dataframe based on the OpenAI response (optional)
        return df  # Modify this as needed to integrate OpenAI response into the dataframe

    except Exception as e:
        st.error(f"OpenAI request failed: {e}")
        return df
