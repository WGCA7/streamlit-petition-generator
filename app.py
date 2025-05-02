# STREAMLIT APP: Polished UI for Petitions + Discovery

import streamlit as st
import openai
import requests
from docx import Document
from io import BytesIO
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
import json

USERNAME = "admin"
PASSWORD = "letmein123"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("Secure Legal Document Generator")
    st.markdown("Please log in to access the automation tool.")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == USERNAME and pw == PASSWORD:
            st.session_state["authenticated"] = True
        else:
            st.error("Incorrect username or password.")
    st.stop()

if st.session_state["authenticated"]:
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    st.title("Document Automation Portal")
    st.markdown("---")

    st.header("📄 Petition & Template Generator")

    TEMPLATE_MAP = {
        "Petitions": {
            "MVA – 1 Defendant": "petition_mva_1def.docx",
            "MVA – 2 Defendants": "petition_mva_2def.docx",
            "Premises Liability": "petition_premises.docx"
        },
        "Discovery": {
            "Plaintiff’s Initial Disclosures": "plaintiff_initial_disclosures.docx",
            "Request for Disclosure": "request_for_disclosure.docx"
        }
    }

    with st.expander("🔍 Select Document Type"):
        category = st.selectbox("Choose Document Category", ["Petitions", "Discovery"])
        doc_type = st.selectbox("Choose Document Type", list(TEMPLATE_MAP[category].keys()))
        template_path = Path("templates") / TEMPLATE_MAP[category][doc_type]

    st.markdown("---")
    st.subheader("📁 Case Information")
    search_type = st.radio("Search by", ["Case ID", "Client Name"])
    case_data = {}

    if search_type == "Case ID":
        case_id = st.text_input("Enter Case ID")
        if case_id:
            st.success(f"Simulated pull of case data for Case ID: {case_id}")
            case_data = {"client": {"name": "Jane Sample"}, "defendant": {"name": "XYZ Corp"}}
    else:
        client_name = st.text_input("Enter Client Name")
        if client_name:
            case_options = [f"{client_name} – Case {i}" for i in range(1, 4)]
            selected = st.selectbox("Select Matching Case", case_options)
            st.success(f"Simulated pull of case data for {selected}")
            case_data = {"client": {"name": client_name}, "defendant": {"name": "XYZ Corp"}}

    st.markdown("---")

    if case_data and category == "Discovery":
        st.subheader("⚖️ Discovery Drafting Options")
        doc_purpose = st.radio("Are you drafting or answering?", ["Answering Opposing Counsel Requests", "Drafting Our Requests"])
        discovery_type = st.selectbox("Select Discovery Type", [
            "Request for Admissions",
            "Request for Production",
            "Interrogatories",
            "Request for Disclosure"
        ])
        uploaded_file = st.file_uploader("Upload Discovery Document (.docx)", type=["docx"])

        if uploaded_file:
            discovery_doc = Document(uploaded_file)
            case_facts = f"Case details: {case_data}. Use this information when crafting your response."

            output_doc = Document()
            title = ("Plaintiff's Responses to Opposing Counsel's Discovery Requests"
                     if doc_purpose == "Answering Opposing Counsel Requests"
                     else "Plaintiff's Discovery Requests to Opposing Counsel")
            output_doc.add_heading(title, 0)

            for para in discovery_doc.paragraphs:
                if para.text.strip():
                    prefix = "[RFA]" if "admit" in para.text.lower() else "[ROG]" if "describe" in para.text.lower() or "explain" in para.text.lower() else "[RFP]" if "produce" in para.text.lower() else "[DISCOVERY]"
                    if doc_purpose == "Answering Opposing Counsel Requests":
                        prompt = f"Respond to the following {prefix} based on the facts of a Texas personal injury case: '{para.text.strip()}'. {case_facts}"
                        system_role = "You are a Texas litigation paralegal drafting discovery responses."
                    else:
                        prompt = f"Draft a well-phrased {prefix} for a Texas personal injury case that covers: '{para.text.strip()}'. {case_facts}"
                        system_role = "You are a Texas litigation paralegal drafting discovery requests."

                    try:
                        ai_response = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": system_role},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        answer = ai_response['choices'][0]['message']['content']
                        output_doc.add_paragraph(f"{prefix} {para.text.strip()}", style='List Number')
                        output_doc.add_paragraph(f"{answer}")
                    except Exception as e:
                        output_doc.add_paragraph(f"{prefix} {para.text.strip()}", style='List Number')
                        output_doc.add_paragraph(f"[Error generating response: {str(e)}]")

            output_buffer = BytesIO()
            output_doc.save(output_buffer)
            output_buffer.seek(0)
            st.download_button(
                f"Download Discovery {doc_purpose.split()[0]} as Word Document",
                data=output_buffer,
                file_name=f"discovery_{discovery_type.replace(' ', '_').lower()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )






