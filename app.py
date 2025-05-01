import streamlit as st
import openai
import requests
from docx import Document
from io import BytesIO
from dotenv import load_dotenv
import os
from pathlib import Path

# ---- Login Section ----
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
    # Load environment variables
    load_dotenv()
    CASEPEER_API_KEY = os.getenv("CASEPEER_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    openai.api_key = OPENAI_API_KEY

    # Set headers for CasePeer
    HEADERS = {
        "Authorization": f"Token {CASEPEER_API_KEY}",
        "Content-Type": "application/json"
    }

    def get_case_data(case_id):
        url = f"https://api.casepeer.com/v1/cases/{case_id}"
        response = requests.get(url, headers=HEADERS)
        return response.json()

    def get_all_cases():
        url = "https://api.casepeer.com/v1/cases/"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch cases from CasePeer.")
            return []

    def generate_factual_background(incident_date, location, injuries, treatment):
        prompt = (
            f"Draft the 'Factual Background' section of a Texas personal injury petition. "
            f"The accident occurred on {incident_date} at {location}. "
            f"The plaintiff reported the following injuries: {injuries}. "
            f"Treatment included: {treatment}. Write this in a formal legal tone."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def generate_venue_paragraph(incident_county, defendant_county, plaintiff_county):
        prompt = (
            "You are drafting the 'Jurisdiction and Venue' section of a Texas personal injury petition. "
            "Refer to Section 15.002 of the Texas Civil Practice and Remedies Code. "
            f"The incident occurred in {incident_county} County. "
            f"The defendant resides in {defendant_county} County. "
            f"The plaintiff resides in {plaintiff_county} County. "
            "If multiple venue options are proper, select the one most favorable to Plaintiff and explain why venue is proper."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def fill_template(template_path, context):
        doc = Document(template_path)
        for para in doc.paragraphs:
            for key, val in context.items():
                if f"«{key}»" in para.text:
                    para.text = para.text.replace(f"«{key}»", val)
        return doc

    st.title("Texas Petition Generator from CasePeer")
    petition_type = st.selectbox("Select Petition Type", [
        "Motor Vehicle Accident – Single Defendant",
        "Motor Vehicle Accident – Multiple Defendants",
        "Premises Liability"
    ])

    use_name_search = st.checkbox("Search by client name instead of Case ID")
    case = None

    if use_name_search:
        client_name = st.text_input("Client Full Name (First Last):")
        if client_name:
            all_cases = get_all_cases()
            matching_cases = [case for case in all_cases if f"{case['client']['first_name']} {case['client']['last_name']}".lower() == client_name.lower()]

if matching_cases:
    if len(matching_cases) == 1:
        case = get_case_data(matching_cases[0]['id'])
    else:
        selection = st.selectbox(
            "Multiple matches found. Select the correct case:",
            [f"{c['client']['first_name']} {c['client']['last_name']} (Case ID: {c['id']})" for c in matching_cases]
        )
        selected_id = int(selection.split("Case ID: ")[1].replace(")", ""))
        case = get_case_data(selected_id)
else:
    st.warning("No matching case found for that client name.")

            if matching_case:
                case = get_case_data(matching_case['id'])
            else:
                st.warning("No matching case found for that client name.")
    else:
        case_id = st.text_input("Enter CasePeer Case ID:")
        if case_id:
            case = get_case_data(case_id)

    if case:
        template_path = Path(__file__).parent / "templates" / "petition_template.docx"

        plaintiff = case.get("client", {})
        defendants = case.get("defendants", [])

        plaintiff_name = f"{plaintiff.get('first_name', '')} {plaintiff.get('last_name', '')}"
        plaintiff_last_name = plaintiff.get("last_name", "")
        plaintiff_address = f"{plaintiff.get('address_line_1', '')}, {plaintiff.get('city', '')}, {plaintiff.get('state', '')} {plaintiff.get('zip', '')}"
        plaintiff_county = plaintiff.get("county", "")

        if petition_type == "Motor Vehicle Accident – Multiple Defendants" and len(defendants) > 1:
            defendant_names = [d.get("name", "Unknown Defendant") for d in defendants]
            combined_defendant_name = " and ".join(defendant_names)
            defendant_last_name = "Defendants"
            defendant_address = "; ".join([
                f"{d.get('address_line_1', '')}, {d.get('city', '')}, {d.get('state', '')} {d.get('zip', '')}"
                for d in defendants
            ])
            defendant_county = defendants[0].get("county", plaintiff_county)
        else:
            defendant = defendants[0] if defendants else {}
            combined_defendant_name = defendant.get("name", "Unknown Defendant")
            defendant_last_name = combined_defendant_name.split()[-1]
            defendant_address = f"{defendant.get('address_line_1', '')}, {defendant.get('city', '')}, {defendant.get('state', '')} {defendant.get('zip', '')}"
            defendant_county = defendant.get("county", plaintiff_county)

        incident_date = case.get("incident_date", "")
        incident_location = case.get("incident_location_description", "")
        injuries = case.get("injury_summary", "")
        treatment = case.get("treatment_summary", "")

        factual_background = generate_factual_background(incident_date, incident_location, injuries, treatment)
        venue_paragraph = generate_venue_paragraph(incident_county=plaintiff_county, defendant_county=defendant_county, plaintiff_county=plaintiff_county)

        context = {
            "PlaintiffName": plaintiff_name,
            "PlaintiffLastName": plaintiff_last_name,
            "PlaintiffAddress": plaintiff_address,
            "PlaintiffCounty": plaintiff_county,
            "DefendantName": combined_defendant_name,
            "DefendantLastName": defendant_last_name,
            "DefendantAddress": defendant_address,
            "DefendantCounty": defendant_county,
            "VenueParagraph": venue_paragraph,
            "FactualBackground": factual_background,
            "County": plaintiff_county
        }

        doc = fill_template(template_path, context)
        output = BytesIO()
        doc.save(output)
        output.seek(0)

        st.download_button("Download Filled Petition", output, file_name="Generated_Petition.docx")

