import streamlit as st
import os

# Import your three modular components
from Text_Extraction import ResumeParser
from Text_Conversion import convert_to_json_with_gpt
from Placeholder_Insertion import generate_resume

def main():
    """
    Main function to run the Streamlit application.
    This orchestrates the three steps:
    1. Extract text from an uploaded resume.
    2. Convert the text to structured JSON using an AI model.
    3. Generate a new .docx resume using the parsed data and a local template.
    """
    st.set_page_config(layout="wide", page_title="AI Resume Builder")
    
    # --- HEADER ---
    st.title("📄 AI-Powered Resume Builder")
    st.markdown("This tool extracts information from any resume (PDF, DOCX, image) and rebuilds it using a standardized company template.")
    st.divider()

    # --- API KEY HANDLING ---
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("🛑 OPENAI_API_KEY not found in Streamlit Secrets.")
        st.info("Please add your OpenAI API key to the Streamlit secrets to run this app. See the README for instructions.")
        st.stop()

    # --- DEFINE TEMPLATE PATH ---
    template_path = "template table.docx"
    if not os.path.exists(template_path):
        st.error(f"🛑 Template file not found at '{template_path}'.")
        st.info("Please make sure 'template table.docx' is in the same directory as this app.")
        st.stop()

    # --- INITIALIZE SESSION STATE ---
    if "extracted_text" not in st.session_state:
        st.session_state.extracted_text = None
    if "parsed_data" not in st.session_state:
        st.session_state.parsed_data = None
    # NEW: Add a session state to hold the generated document buffer
    if "generated_doc_buffer" not in st.session_state:
        st.session_state.generated_doc_buffer = None


    # --- UI LAYOUT AND WORKFLOW ---
    st.header("Step 1: Upload a Resume and Convert")

    # --- Use a form to group the uploader and the button ---
    with st.form(key="resume_form"):
        uploaded_resume = st.file_uploader(
            "Upload a resume file to extract its content.",
            type=["pdf", "docx", "png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )
        
        # --- NEW: The "Convert" button that submits the form ---
        submitted = st.form_submit_button(
            "Convert Resume", 
            type="primary", 
            use_container_width=True
        )

    # --- This block now only runs AFTER the "Convert" button is clicked ---
    if submitted and uploaded_resume:
        # Clear previous results before starting a new run
        st.session_state.extracted_text = None
        st.session_state.parsed_data = None
        st.session_state.generated_doc_buffer = None

        with st.spinner("Step 1/3: Reading resume file..."):
            parser = ResumeParser()
            st.session_state.extracted_text = parser.read_file(uploaded_resume)

        if st.session_state.extracted_text:
            with st.spinner("Step 2/3: Analyzing resume with AI..."):
                st.session_state.parsed_data = convert_to_json_with_gpt(
                    st.session_state.extracted_text, api_key
                )
        
        if st.session_state.parsed_data:
            with st.spinner("Step 3/3: Generating new resume from template..."):
                st.session_state.generated_doc_buffer = generate_resume(st.session_state.parsed_data, template_path)
    
    # --- NEW: This section is now outside the processing block ---
    # It will always show the download button if a document has been generated.
    if st.session_state.generated_doc_buffer:
        st.success("🎉 Resume processed and new document generated!")
        
        st.download_button(
            label="⬇️ Download Generated Resume",
            data=st.session_state.generated_doc_buffer,
            # Output File Name
            file_name=f"_Resume_{st.session_state.parsed_data.get('name', 'candidate').replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            type="primary"
        )
    # Handle the case where the final step fails after processing
    elif submitted and not st.session_state.generated_doc_buffer:
         st.error("Processing complete, but failed to generate the final document.")


    st.divider()

#def uncomment():
#Comment the above function to show text & JSON
    # --- Display Results Section (No changes needed here) ---
    st.header("Processing Results")
    if not uploaded_resume:
        st.info("Upload a resume and click 'Convert' to see the results here.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Raw Extracted Text")
        if st.session_state.extracted_text:
            st.text_area("Extracted Text", st.session_state.extracted_text, height=400, label_visibility="collapsed")
        else:
            st.text_area("Extracted Text", "Text from the uploaded resume will appear here.", height=400, label_visibility="collapsed", disabled=True)

    with col2:
        st.subheader("AI-Parsed JSON Data")
        if st.session_state.parsed_data:
            st.json(st.session_state.parsed_data)
        else:
             #Display an empty-looking JSON object as a placeholder
            st.json({})
   
if __name__ == "__main__":
    main()
