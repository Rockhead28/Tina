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
You are a resume parser. Extract the following structured fields from the resume text below and return ONLY a valid JSON object.

Required fields:
- name
- contact_number
- email
- skills (as a list)
- languages
- education: list of {{education certificate}}
- work_experience: list of {{
    company_name (reformat font to only capitalize first letter as capital),
    duration,
    job_title,
    job_description (as a list),
    achievements (if available)
}}

Make sure work_experience is a list of entries, and fields like skills or job_description are lists, not strings.

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
