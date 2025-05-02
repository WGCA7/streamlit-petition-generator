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

    TEMPLATE_MAP = {
        "Petitions": {
            "MVA – 1 Defendant": "petition_mva_1def.docx",
            "MVA – 2 Defendants": "petition_mva_2def.docx",
            "Premises Liability": "petition_premises.docx"
        },
        "Discovery Responses": {
            "Requests for Admission (RFAs)": "rfa_response.docx",
            "Requests for Production (RFPs)": "rfp_response.docx",
            "Interrogatories (ROGs)": "rog_response.docx"
        },
        "Demand & Settlement": {
            "Demand Letter": "demand_letter.docx",
            "Settlement Breakdown": "settlement_breakdown.docx"
        },
        "Medical Documents": {
            "Letter of Protection (LOP)": "lop_template.docx"
        },
        "Insurance Communications": {
            "Letter of Representation (LOR)": "lor.docx"
        }
    }

    category = st.selectbox("Choose Document Category", list(TEMPLATE_MAP.keys()))
    doc_type = st.selectbox("Choose Document Type", list(TEMPLATE_MAP[category].keys()))
    template_path = Path(__file__).parent / "templates" / TEMPLATE_MAP[category][doc_type]

    case_id = st.text_input("Enter CasePeer Case ID:")
    if case_id:
        case_url = f"https://api.casepeer.com/v1/cases/{case_id}"
        response = requests.get(case_url, headers=HEADERS)

        if response.status_code == 200:
            case = response.json()
            st.success("Case retrieved successfully. Template ready to fill.")
            st.write(f"You selected: {doc_type}")

            # Fetch treatments for LOP
            provider_name = ""
            provider_address = ""
            if doc_type == "Letter of Protection (LOP)":
                treatment_url = f"https://api.casepeer.com/v1/cases/{case_id}/treatments"
                treatment_response = requests.get(treatment_url, headers=HEADERS)
                if treatment_response.status_code == 200:
                    treatments = treatment_response.json()
                    provider_names = list(set(t["provider_name"] for t in treatments if "provider_name" in t))
                    selected_provider = st.selectbox("Select Provider for LOP", provider_names)
                    provider_name = selected_provider
                    for t in treatments:
                        if t.get("provider_name") == selected_provider:
                            provider_address = t.get("provider_address", "")
                            break
                else:
                    st.warning("Unable to retrieve provider list.")

            defendant_address = case.get("defendant", {}).get("address")
            inferred_county = get_county_from_address(defendant_address)

            # Fallback to incident address if defendant county not found
            if not inferred_county:
                incident_address = case.get("incident_address") or case.get("incident", {}).get("address")
                inferred_county = get_county_from_address(incident_address)

            placeholders = {
                "«PlaintiffName»": case.get("client", {}).get("name", "[PLAINTIFF]"),
                "«DefendantName»": case.get("defendant", {}).get("name", "[DEFENDANT]"),
                "«FactualBackground»": "",
                "«VenueParagraph»": "",
                "«RepresentationReason»": "",
                "«ProviderName»": provider_name or "[PROVIDER]",
                "«ProviderAddress»": provider_address or "[ADDRESS]",
                "«DateGenerated»": datetime.today().strftime('%B %d, %Y'),
                "«DefendantCounty»": inferred_county or "[COUNTY]"
            }

            try:
                background_prompt = f"Generate a factual background paragraph for a personal injury case with the following details: {case}"
                background_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a legal drafting assistant."},
                        {"role": "user", "content": background_prompt}
                    ]
                )
                placeholders["«FactualBackground»"] = background_response['choices'][0]['message']['content']
            except Exception as e:
                st.warning(f"GPT generation failed for Factual Background: {e}")

            try:
                venue_prompt = f"Draft a jurisdiction and venue paragraph for a Texas personal injury case using this county: {inferred_county}, and these case details: {case}"
                venue_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a legal drafting assistant."},
                        {"role": "user", "content": venue_prompt}
                    ]
                )
                placeholders["«VenueParagraph»"] = venue_response['choices'][0]['message']['content']
            except Exception as e:
                st.warning(f"GPT generation failed for Venue Paragraph: {e}")

            if doc_type == "Letter of Representation (LOR)":
                try:
                    lor_prompt = f"Draft a short paragraph for a Letter of Representation sent to an insurer in a personal injury case. Use the following details: {case}"
                    lor_response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a legal assistant drafting insurance correspondence."},
                            {"role": "user", "content": lor_prompt}
                        ]
                    )
                    placeholders["«RepresentationReason»"] = lor_response['choices'][0]['message']['content']
                except Exception as e:
                    st.warning(f"GPT generation failed for LOR content: {e}")

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

        else:
            st.error("Failed to retrieve case. Check Case ID or API key.")


