import streamlit as st
import openai
import requests
from docx import Document
from io import BytesIO
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime

USERNAME = "admin"
PASSWORD = "letmein123"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
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
    CASEPEER_API_KEY = os.getenv("CASEPEER_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    openai.api_key = OPENAI_API_KEY

    HEADERS = {
        "Authorization": f"Token {CASEPEER_API_KEY}",
        "Content-Type": "application/json"
    }

    def get_county_from_address(address):
        if not GOOGLE_API_KEY or not address:
            return None
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": GOOGLE_API_KEY}
        response = requests.get(geocode_url, params=params)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                components = results[0].get("address_components", [])
                for comp in components:
                    if "administrative_area_level_2" in comp.get("types", []):
                        return comp.get("long_name")
        return None

    st.header("Document Automation Portal")
    section = st.selectbox("Choose Function", ["Petition & Template Generator", "Discovery Drafting & Responses"])

    if section == "Discovery Drafting & Responses":
        doc_type = st.radio("Are you drafting requests or answering requests?", ["Answering OC Requests", "Drafting Our Requests"])
        uploaded_file = st.file_uploader("Upload Discovery Document (.docx)", type=["docx"])
        case_id = st.text_input("Enter CasePeer Case ID (optional):")

        if uploaded_file:
            discovery_doc = Document(uploaded_file)
            case_data = {}
            if case_id:
                case_url = f"https://api.casepeer.com/v1/cases/{case_id}"
                response = requests.get(case_url, headers=HEADERS)
                case_data = response.json() if response.status_code == 200 else {}
            case_facts = f"Case details: {case_data}. Use this information when crafting your response."

            output_doc = Document()
            if doc_type == "Answering OC Requests":
                output_doc.add_heading("Plaintiff's Responses to Defendant's Discovery Requests", 0)
            else:
                output_doc.add_heading("Plaintiff's Discovery Requests to Defendant", 0)

            for para in discovery_doc.paragraphs:
                if para.text.strip():
                    prefix = "[RFA]" if "admit" in para.text.lower() else "[ROG]" if "describe" in para.text.lower() or "explain" in para.text.lower() else "[RFP]" if "produce" in para.text.lower() or "documents" in para.text.lower() else "[DISCOVERY]"

                    if doc_type == "Answering OC Requests":
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

            file_label = "responses" if doc_type == "Answering OC Requests" else "requests"
            st.download_button(
                f"Download Discovery {file_label.title()} as Word Document",
                data=output_buffer,
                file_name=f"discovery_{file_label}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    elif section == "Petition & Template Generator":
        st.subheader("Generate Petition or Other Template-Based Document")
        TEMPLATE_MAP = {
            "Discovery": {
                "Plaintiff’s Initial Disclosures": "plaintiff_initial_disclosures.docx",
                "Request for Disclosure": "request_for_disclosure.docx"
            },
            "Petitions": {
                "MVA – 1 Defendant": "petition_mva_1def.docx",
                "MVA – 2 Defendants": "petition_mva_2def.docx",
                "Premises Liability": "petition_premises.docx"
            },
            "Medical": {
                "Letter of Protection (LOP)": "lop_template.docx"
            },
            "Insurance": {
                "Letter of Representation (LOR)": "lor.docx"
            }
        }

        category = st.selectbox("Choose Document Category", list(TEMPLATE_MAP.keys()))
        doc_type = st.selectbox("Choose Document Type", list(TEMPLATE_MAP[category].keys()))
        template_path = Path("templates") / TEMPLATE_MAP[category][doc_type]

        case_id = st.text_input("Enter CasePeer Case ID for Template Generation:")

        if case_id:
            case_url = f"https://api.casepeer.com/v1/cases/{case_id}"
            response = requests.get(case_url, headers=HEADERS)
            case = response.json() if response.status_code == 200 else {}

            defendant_address = case.get("defendant", {}).get("address")
            inferred_county = get_county_from_address(defendant_address)
            if not inferred_county:
                incident_address = case.get("incident_address") or case.get("incident", {}).get("address")
                inferred_county = get_county_from_address(incident_address)

            placeholders = {
                "«PlaintiffName»": case.get("client", {}).get("name", "[PLAINTIFF]"),
                "«DefendantName»": case.get("defendant", {}).get("name", "[DEFENDANT]"),
                "«FactualBackground»": "",
                "«VenueParagraph»": "",
                "«RepresentationReason»": "",
                "«DefendantCounty»": inferred_county or "[COUNTY]",
                "«DateGenerated»": datetime.today().strftime('%B %d, %Y')
            }

            try:
                background_prompt = f"Generate a factual background paragraph for a Texas personal injury case using this data: {case}"
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a legal drafting assistant."},
                        {"role": "user", "content": background_prompt}
                    ]
                )
                placeholders["«FactualBackground»"] = response['choices'][0]['message']['content']
            except Exception as e:
                st.warning(f"Factual background error: {e}")

            try:
                venue_prompt = f"Draft a venue paragraph for a Texas personal injury case. County: {inferred_county}. Case details: {case}"
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a legal drafting assistant."},
                        {"role": "user", "content": venue_prompt}
                    ]
                )
                placeholders["«VenueParagraph»"] = response['choices'][0]['message']['content']
            except Exception as e:
                st.warning(f"Venue paragraph error: {e}")

            if doc_type == "Letter of Representation (LOR)":
                try:
                    lor_prompt = f"Draft a short Letter of Representation based on: {case}"
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a legal assistant drafting insurance correspondence."},
                            {"role": "user", "content": lor_prompt}
                        ]
                    )
                    placeholders["«RepresentationReason»"] = response['choices'][0]['message']['content']
                except Exception as e:
                    st.warning(f"LOR generation error: {e}")

            doc = Document(template_path)
            for para in doc.paragraphs:
                for key, value in placeholders.items():
                    if key in para.text:
                        para.text = para.text.replace(key, value)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            st.download_button(
                label="Download Completed Document",
                data=buffer,
                file_name=f"{doc_type.replace(' ', '_').lower()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )




