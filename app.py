import streamlit as st
import requests
import json
import os
from docx import Document
from io import BytesIO
from legal_template_binding import generate_final_document  # Backend import to use the final document generation

st.set_page_config(page_title="Legal Document Generator", layout="wide")
st.title("📄 Legal Document Automation")
st.divider()

# --- Template Maps ---
petition_doc_map = {
    "MVA - 1 Defendant Original Petition": "mva_1_defendant_original_petition",
    "MVA - 2 Defendants Original Petition": "mva_2_defendants_original_petition",
    "Premises Liability Original Petition": "premises_liability_original_petition",
    "Wrongful Death Original Petition": "wrongful_death_original_petition",
    "Dog Bite Original Petition": "dog_bite_original_petition",
    "Medical Malpractice Original Petition": "medical_malpractice_original_petition"
}

requests_doc_map = {
    "Plaintiff's Request for Initial Disclosures": "initial_disclosures",
    "Plaintiff's Interrogatories to Defendant": "interrogatories",
    "Plaintiff's Request for Admissions": "request_for_admissions",
    "Plaintiff's Request for Production": "request_for_production",
}

answers_doc_map = {
    "Plaintiff’s Response to Defendant’s Request for Disclosures": "answer_to_request_for_disclosures",
    "Answer to Interrogatories": "answer_to_interrogatories",
    "Answer to Request for Admissions": "answer_to_request_for_admissions",
    "Answer to Request for Production": "answer_to_request_for_production",
}

demand_letters = {
    "Stowers Demand Letter": "stowers_demand_letter",
    "General Demand Letter": "demand_letter",
    "Motor Vehicle Accident Demand Letter": "motor_vehicle_demand_letter",
    "Uninsured/Underinsured Motorist Demand Letter": "um_uim_demand_letter",
    "Slip and Fall Demand Letter": "slip_and_fall_demand_letter",
    "Dog Bite Demand Letter": "dog_bite_demand_letter"
}

insurance_docs = {
    "Letter of Representation": "letter_of_representation",
    "Uninsured/Underinsured Letter of Representation": "um_uim_letter_of_representation"
}

medical_docs = {
    "Letter of Protection": "letter_of_protection"
}

# --- Document Category Selection ---
st.subheader("📂 Document Type")
selected_template_key = None
selected_doc_category = st.selectbox(
    "Choose Document Category:",
    ["Petitions", "Discovery", "Demand Letters", "Insurance", "Medical"]
)

if selected_doc_category == "Petitions":
    selected_petition_doc = st.selectbox("Select Petition Template:", list(petition_doc_map.keys()))
    selected_template_key = petition_doc_map[selected_petition_doc]
elif selected_doc_category == "Discovery":
    discovery_type = st.radio("Select Discovery Task:", ["Documents to Request", "Answering Opposing Counsel Requests"])
    if discovery_type == "Documents to Request":
        selected_discovery_doc = st.selectbox("Select Document to Request:", list(requests_doc_map.keys()))
        selected_template_key = requests_doc_map[selected_discovery_doc]
    else:
        selected_discovery_doc = st.selectbox("Select Document to Answer:", list(answers_doc_map.keys()))
        selected_template_key = answers_doc_map[selected_discovery_doc]
elif selected_doc_category == "Demand Letters":
    selected_demand_doc = st.selectbox("Select Demand Letter Type:", list(demand_letters.keys()))
    selected_template_key = demand_letters[selected_demand_doc]
elif selected_doc_category == "Insurance":
    selected_insurance_doc = st.selectbox("Select Insurance Document:", list(insurance_docs.keys()))
    selected_template_key = insurance_docs[selected_insurance_doc]
elif selected_doc_category == "Medical":
    selected_medical_doc = st.selectbox("Select Medical Document:", list(medical_docs.keys()))
    selected_template_key = medical_docs[selected_medical_doc]

st.divider()

# --- Client Lookup via Zapier Webhook ---
st.subheader("🔎 Search for Client by Name")

zapier_url = "https://streamlit-webhook-backend.onrender.com/receive"
case_id = st.text_input("Enter Case ID (optional)")
first_name = st.text_input("Client First Name")
last_name = st.text_input("Client Last Name")

if st.button("🔍 Search Clients"):
    if case_id:
        try:
            response = requests.post(zapier_url, json={"case_id": case_id})
            if response.status_code == 200:
                st.success("✅ Case ID sent to Zapier. Awaiting CasePeer data...")
            else:
                st.error(f"❌ Failed to send case ID. Status code: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Could not reach Zapier: {e}")
    elif not first_name or not last_name:
        st.warning("Please enter both first and last name or a Case ID.")
    else:
        try:
            response = requests.post(zapier_url, json={"first_name": first_name, "last_name": last_name})
            if response.status_code == 200:
                st.success("✅ Name-based request sent. Reload shortly to fetch data.")
            else:
                st.error("❌ Name search failed.")
        except Exception as e:
            st.error(f"❌ Zapier request error: {e}")

# --- Webhook Refresh ---
st.subheader("🔄 Refresh Webhook Data")
if "webhook_data" not in st.session_state:
    st.session_state["webhook_data"] = {}

if st.button("🔄 Reload Webhook Data"):
    try:
        response = requests.get("https://streamlit-webhook-backend.onrender.com/latest")
        if response.status_code == 200:
            webhook_data = response.json()
            if "error" not in webhook_data:
                st.session_state["webhook_data"] = webhook_data
                st.success("✅ Webhook data refreshed.")
            else:
                st.warning("⚠️ No data found in webhook.")
        else:
            st.error(f"❌ Webhook status: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Could not contact webhook: {e}")

# --- Manual Input Fields ---
st.divider()
st.subheader("📝 Input Client Information Manually")

# Pull webhook data for prefill
webhook_data = st.session_state.get("webhook_data", {})

def get_prefill_value(label):
    return webhook_data.get(label.lower().replace(" ", "_"), "")

PLACEHOLDER_SCHEMA = {
    "Client Info": {
        "[CLIENT_NAME]": "Client Name",
        "[CLIENT_DOB]": "Date of Birth",
        "[CLIENT_PHONE]": "Phone Number",
        "[CLIENT_ADDRESS]": "Client Address",
        "[CLIENT_COUNTY]": "Client County"
    },
    "Accident Info": {
        "[DATE_OF_ACCIDENT]": "Date of Accident",
        "[LOCATION_OF_ACCIDENT]": "Accident Location",
        "[POLICE_REPORT_NUMBER]": "Police Report Number"
    },
    "Attorney Info": {
        "[ATTORNEY_NAME]": "Attorney Name",
        "[FIRM_NAME]": "Firm Name"
    },
    "Insurance Info": {
        "[INSURANCE_COMPANY]": "Insurance Company",
        "[CLAIM_NUMBER]": "Claim Number"
    },
    "Legal Content": {
        "[FACTUAL_BACKGROUND]": "Factual Background",
        "[VENUE_AND_JURISDICTION]": "Venue & Jurisdiction",
        "[NEGLIGENCE_ALLEGATIONS]": "Negligence Allegations",
        "[PRAYER]": "Prayer",
        "[DAMAGES_SUMMARY]": "Damages Summary"
    },
    "Defendant Info": {
        "[DEFENDANT_1_NAME]": "Defendant 1 Name",
        "[DEFENDANT_1_ADDRESS]": "Defendant 1 Address",
        "[DEFENDANT_1_INSURANCE]": "Defendant 1 Insurance Carrier",
        "[DEFENDANT_2_NAME]": "Defendant 2 Name (if applicable)",
        "[DEFENDANT_2_ADDRESS]": "Defendant 2 Address (if applicable)",
        "[DEFENDANT_2_INSURANCE]": "Defendant 2 Insurance Carrier (if applicable)"
    }
}

replacements = {}
for section, fields in PLACEHOLDER_SCHEMA.items():
    with st.expander(f"📂 {section}"):
        show_extra = True
        if section == "Defendant Info":
            show_extra = st.checkbox("Include Second Defendant?", key="show_def2")

        for placeholder, label in fields.items():
            if "DEFENDANT_2" in placeholder and not st.session_state.get("show_def2", False):
                continue
            default_val = get_prefill_value(label)
            value = st.text_input(label, value=default_val, key=placeholder)
            replacements[placeholder] = value

# Store user-entered fields in session for backup
st.session_state["manual_inputs"] = replacements

# --- GPT Section Generator ---
st.divider()
GPT_SECTION_PROMPTS = {
    "[FACTUAL_BACKGROUND]": {
        "label": "Factual Background",
        "prompt": "Draft a factual background section based on the following case facts:"
    },
    "[VENUE_AND_JURISDICTION]": {
        "label": "Venue & Jurisdiction",
        "prompt": "Explain the appropriate venue and jurisdiction for this case:"
    },
    "[NEGLIGENCE_ALLEGATIONS]": {
        "label": "Negligence Allegations",
        "prompt": "List the negligence allegations against the defendant:"
    },
    "[PRAYER]": {
        "label": "Prayer for Relief",
        "prompt": "Draft a standard prayer for relief in a personal injury petition:"
    }
}

with st.expander("🧠 AI Section Generator (Factual Background, Venue, Negligence, Prayer)"):
    if "gpt_sections" not in st.session_state:
        st.session_state["gpt_sections"] = {}

    for placeholder, meta in GPT_SECTION_PROMPTS.items():
        context = st.text_area(f"✍️ {meta['label']} - Context:", key=f"ctx_{placeholder}")
        if st.button(f"Generate {meta['label']}", key=f"gen_{placeholder}"):
            result = f"[Generated Section for {meta['label']}]\n\n{context}"
            st.session_state["gpt_sections"][placeholder] = result

        if placeholder in st.session_state["gpt_sections"]:
            st.text_area(
                f"🧠 {meta['label']} Output",
                st.session_state["gpt_sections"][placeholder],
                height=200,
                key=f"out_{placeholder}"
            )

# --- Venue & Jurisdiction Generator ---
st.divider()
with st.expander("📍 Venue & Jurisdiction Generator"):
    venue_zip = st.text_input("ZIP code of accident (optional)")
    defendant_county = st.text_input("Defendant residence county (optional)")
    office_county = st.text_input("Defendant principal office county (optional)")

    def generate_venue(acc_county, def_county, office_county):
        parts = []
        if acc_county:
            parts.append(f"under CPRC §15.002(a)(1) because a substantial part of the events occurred in {acc_county} County")
        if def_county:
            parts.append(f"under §15.002(a)(2) because Defendant resides in {def_county} County")
        if office_county:
            parts.append(f"under §15.002(a)(3) because Defendant’s principal office is in {office_county} County")
        return f"Venue is proper in {acc_county or '______'} County, Texas — " + "; ".join(parts) + "."

    if st.button("Generate Venue Narrative"):
        acc_county = "Harris" if venue_zip == "77002" else "Unknown"
        result = generate_venue(acc_county, defendant_county, office_county)
        st.text_area("Generated Venue Text", result, height=200)

# --- Final Document Generation & Download ---
st.divider()
st.subheader("📥 Generate Final Document")

if selected_template_key:
    webhook_data = st.session_state.get("webhook_data", {})

    # Merge in manual overrides
    if "manual_inputs" in st.session_state:
        webhook_data.update({
            k.lower().replace(" ", "_"): v for k, v in st.session_state["manual_inputs"].items()
        })

    # Add GPT-filled content
    if "gpt_sections" in st.session_state:
        webhook_data.update({
            k.lower().replace(" ", "_"): v for k, v in st.session_state["gpt_sections"].items()
        })

    try:
        buffer = generate_final_document(selected_template_key, webhook_data)

        if st.button("📄 Preview Document Text"):
            doc = Document(BytesIO(buffer.getvalue()))
            preview = "\n".join(p.text for p in doc.paragraphs)
            st.text_area("📄 Preview Output", preview, height=400)

        st.download_button(
            label="📥 Download Final Document",
            data=buffer.getvalue(),
            file_name=f"{selected_template_key}_final.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        st.error(f"❌ Error generating document: {e}")
else:
    st.info("⚠️ Please select a document template from above.")































