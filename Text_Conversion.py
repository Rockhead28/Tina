#!/usr/bin/env python
# coding: utf-8

# # Step 2: Conversion from text to json structured data

# In[ ]:
import json
from typing import Optional

import streamlit as st
from openai import OpenAI

def convert_to_json_with_gpt(resume_text: str, api_key: str) -> Optional[dict]:
    """
    Parses resume text into a structured JSON object using the OpenAI API.
    """
    if not api_key:
        st.error("OpenAI API key is missing.")
        return None

    client = OpenAI(api_key=api_key)

    prompt = f"""
    You are an expert resume parsing system. Your task is to extract structured information from the provided resume text.
    
    You MUST follow these rules:
    1.  Return ONLY a single, valid JSON object. Do not include any introductory text, explanations, or apologies (e.g., "Here is the JSON...").
    2.  All values in the JSON object, including years and GPA, MUST be formatted as strings. This is critical for data type consistency. #<-- Prevents the TypeError
    3.  Adhere strictly to the JSON schema provided below.
    4.  If a field or value is not found in the text, use `null` as the value. Do not make up information.
    
    ### JSON Schema and Formatting:
    - `name`: (string)
    - `contact_number`: (string)
    - `email`: (string)
    - `skills`: (list of strings)
    - `languages`: (list of strings)
    - `nationality`: (strings)
    - `summary`: (strings)
    - `education`: (list of objects)
      - `degree`: (string)
      - `institution`: (string)
      - `year`: (string) 
      - `cgpa`: (string) 
    - `work_experience`: (list of objects)
      - `company_name`: (string, formatted in Title Case)
      - `duration`: (string)
      - `job_title`: (string)
      - `job_description`: (list of strings)
      - `achievements`: (list of strings, use an empty list `[]` if none are found)
    
    Resume text:
    \"\"\"
    {resume_text}
    \"\"\"
    """

    try:
        # Using response_format for reliable JSON output
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        json_output = response.choices[0].message.content
        return json.loads(json_output)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse AI response as JSON. Error: {e}")
        st.info("AI Response that failed to parse:")
        st.code(response.choices[0].message.content, language='text')
        return None
    except Exception as e:
        st.error(f"An error occurred during the GPT API call: {e}")
        return None
