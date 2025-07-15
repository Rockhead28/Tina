import io
from copy import deepcopy
from typing import Optional

import streamlit as st
from docx import Document
from docx.text.paragraph import Paragraph
from docx.text.run import Run

# Your original helper functions (unchanged)
def replace_text_in_paragraph(paragraph: Paragraph, key: str, value: str):
    for run in paragraph.runs:
        if key in run.text:
            run.text = run.text.replace(key, str(value))

def copy_run_formatting(source_run: Run, target_run: Run):
    if source_run is None or target_run is None:
        return
    target_run.font.name = source_run.font.name
    target_run.font.size = source_run.font.size
    target_run.font.bold = source_run.font.bold
    target_run.font.italic = source_run.font.italic
    target_run.font.underline = source_run.font.underline
    if source_run.font.color and source_run.font.color.rgb:
        target_run.font.color.rgb = source_run.font.color.rgb

def copy_paragraph_formatting(source_paragraph: Paragraph, target_paragraph: Paragraph):
    target_paragraph.style = source_paragraph.style
    p_format = source_paragraph.paragraph_format
    target_p_format = target_paragraph.paragraph_format
    target_p_format.alignment = p_format.alignment
    target_p_format.space_after = p_format.space_after
    target_p_format.space_before = p_format.space_before
    target_p_format.left_indent = p_format.left_indent
    target_p_format.right_indent = p_format.right_indent

def replace_with_multiline_text(paragraph: Paragraph, key: str, formatted_text: str):
    lines = formatted_text.split('\n')
    template_run = None
    for run in paragraph.runs:
        if key in run.text:
            template_run = run
            break
    if not template_run:
        return
    template_run.text = template_run.text.replace(key, lines[0])
    for line in lines[1:]:
        template_run.add_break()
        template_run.text += line

def replace_with_bullet_points(paragraph: Paragraph, key: str, bullet_points: list):
    if not bullet_points:
        replace_text_in_paragraph(paragraph, key, "")
        return

    template_run = None
    for run in paragraph.runs:
        if key in run.text:
            template_run = run
            break
    if not template_run:
        return

    parent = paragraph._parent

    if key == "{ACHIEVEMENTS}":
        header_p = parent.add_paragraph()
        copy_paragraph_formatting(paragraph, header_p)
        header_run = header_p.add_run("Achievements:")
        copy_run_formatting(template_run, header_run)
        header_run.bold = True

    paragraph._element.getparent().remove(paragraph._element)

    for point in bullet_points:
        new_p = parent.add_paragraph()
        copy_paragraph_formatting(paragraph, new_p)
        new_run = new_p.add_run("• " + point)
        copy_run_formatting(template_run, new_run)

# Your main function, adapted for Streamlit
def generate_resume(data: dict, template_path: str) -> Optional[io.BytesIO]:
    """
    Generates a resume by populating a .docx template with JSON data.
    This version returns an in-memory buffer for Streamlit.
    """
    try:
        doc = Document(template_path)
    except Exception as e:
        st.error(f"Error opening template file: {e}")
        return None

    # 1. Simple replacements (Your original logic)
    simple_replacements = {
        "{NAME}": data.get("name", ""),
        "{CONTACT}": data.get("contact_number", ""),
        "{EMAIL}": data.get("email", ""),
    }

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for key, value in simple_replacements.items():
                        if key in paragraph.text:
                            replace_text_in_paragraph(paragraph, key, value)

    # 2. Education (Your original logic)
    education_list = data.get("education", [])
    if education_list:
        edu_blocks = []
        for entry in education_list:
            block_lines = []
            if "degree" in entry: block_lines.append(entry["degree"])
            if "institution" in entry: block_lines.append(entry["institution"])
            if "year" in entry: block_lines.append(entry["year"])
            if "cgpa" in entry: block_lines.append(f"CGPA: {entry['cgpa']}")
            edu_blocks.append("\n".join(block_lines))
        formatted_education_string = "\n\n".join(edu_blocks)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        if "{EDUCATION}" in p.text:
                            replace_with_multiline_text(p, "{EDUCATION}", formatted_education_string)

    # 3. Skills and Languages (Your original logic)
    list_replacements = {
        "{SKILLS}": data.get("skills", []),
        "{LANGUAGES}": data.get("languages", [])
    }

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in list(cell.paragraphs):
                    for key, value_list in list_replacements.items():
                        if key in p.text:
                            replace_with_bullet_points(p, key, value_list)

    # 4. Work Experience (Your original logic)
    work_exp_placeholders = {
        "{COMPANYNAME}", "{DURATION}", "{JOBTITLE}",
        "{JOBDESCRIPTION}", "{ACHIEVEMENTS}"
    }

    for table in doc.tables:
        template_rows_info = []
        for i, row in enumerate(table.rows):
            row_text = "".join(cell.text for cell in row.cells)
            if any(ph in row_text for ph in work_exp_placeholders):
                template_rows_info.append({'row': row, 'index': i})

        if not template_rows_info:
            continue

        template_rows = [info['row'] for info in template_rows_info]

        for experience in data.get("work_experience", []):
            for template_row in template_rows:
                new_row_elem = deepcopy(template_row._element)
                table._tbl.append(new_row_elem)
                new_row = table.rows[-1]

                for cell in new_row.cells:
                    for p in list(cell.paragraphs):
                        replace_text_in_paragraph(p, "{COMPANYNAME}", experience.get("company_name", ""))
                        replace_text_in_paragraph(p, "{DURATION}", experience.get("duration", ""))
                        replace_text_in_paragraph(p, "{JOBTITLE}", experience.get("job_title", ""))

                        if "{JOBDESCRIPTION}" in p.text:
                            jd_list = experience.get("job_description", [])
                            replace_with_bullet_points(p, "{JOBDESCRIPTION}", jd_list)
                        
                        if "{ACHIEVEMENTS}" in p.text:
                            achievements_list = experience.get("achievements", [])
                            replace_with_bullet_points(p, "{ACHIEVEMENTS}", achievements_list)

        for template_row in reversed(template_rows):
            tbl = table._tbl
            tbl.remove(template_row._tr)

        break

    # *** THIS IS THE ONLY SIGNIFICANT CHANGE FOR STREAMLIT ***
    # Instead of saving to a file path, save to an in-memory buffer
    try:
        doc_buffer = io.BytesIO()
        doc.save(doc_buffer)
        doc_buffer.seek(0)
        return doc_buffer # Return the buffer for the download button
    except Exception as e:
        st.error(f"Error saving output file to memory: {e}")
        return None
