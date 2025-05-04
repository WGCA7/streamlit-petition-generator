import streamlit as st
import requests
import json
import os
import re
from docx import Document
from io import BytesIO

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

st.title("📄 Legal Document Automation")
st.divider()

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
    st.divider()
elif selected_doc_category == "Discovery":
    discovery_type = st.radio("Select Discovery Task:", ["Documents to Request", "Answering Opposing Counsel Requests"])
    if discovery_type == "Documents to Request":
        selected_discovery_doc = st.selectbox("Select Document to Request:", list(requests_doc_map.keys()))
        selected_template_key = requests_doc_map[selected_discovery_doc]
    else:
        selected_discovery_doc = st.selectbox("Select Document to Answer:", list(answers_doc_map.keys()))
        selected_template_key = answers_doc_map[selected_discovery_doc]
    st.divider()
elif selected_doc_category == "Demand Letters":
    selected_demand_doc = st.selectbox("Select Demand Letter Type:", list(demand_letters.keys()))
    selected_template_key = demand_letters[selected_demand_doc]
    st.divider()
elif selected_doc_category == "Insurance":
    selected_insurance_doc = st.selectbox("Select Insurance Document:", list(insurance_docs.keys()))
    selected_template_key = insurance_docs[selected_insurance_doc]
    st.divider()
elif selected_doc_category == "Medical":
    selected_medical_doc = st.selectbox("Select Medical Document:", list(medical_docs.keys()))
    selected_template_key = medical_docs[selected_medical_doc]
    st.divider()

# --- Client Search ---
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
                st.success("✅ Case ID sent to Zapier successfully. Awaiting CasePeer data...")
            else:
                st.error(f"❌ Failed to send case ID. Status code: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Could not reach Zapier: {e}")
    elif not first_name or not last_name:
        st.warning("Please enter both first and last name or a Case ID.")
    else:
        search_payload = {
            "first_name": first_name,
            "last_name": last_name
        }
        try:
            response = requests.post(zapier_url, json=search_payload)
            if response.status_code == 200:
                st.success("✅ Name-based data sent to Zapier. Please reload the app in a few seconds to pull webhook data.")
            else:
                st.error("❌ Name search failed.")
        except Exception as e:
            st.error(f"❌ Could not contact Zapier: {e}")

# --- Pull Webhook Data from FastAPI ---
st.subheader("🔄 Refresh Webhook Data")
webhook_data = {}

if st.button("🔄 Refresh Webhook Data"):
    try:
        response = requests.get("https://streamlit-webhook-backend.onrender.com/latest")
        if response.status_code == 200:
            webhook_data = response.json()
            if "error" not in webhook_data:
                st.session_state["webhook_data"] = webhook_data
                st.success("✅ Webhook data refreshed.")
            else:
                st.warning("⚠️ No webhook data available yet.")
        else:
            st.error(f"❌ Failed to load data. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Could not contact webhook: {e}")

# Ensure session state key exists
if "webhook_data" not in st.session_state:
    st.session_state["webhook_data"] = {}


# --- GPT Section Generator ---
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
        "prompt": "List the negligence allegations against the defendant based on the following facts:"
    },
    "[PRAYER]": {
        "label": "Prayer for Relief",
        "prompt": "Draft a standard prayer for relief in a personal injury petition:"
    }
}

st.divider()
with st.expander("🧠 AI Section Generator (Factual Background, Venue, Negligence, Prayer)"):
    if "gpt_sections" not in st.session_state:
        st.session_state["gpt_sections"] = {}

    for placeholder, meta in GPT_SECTION_PROMPTS.items():
        st.markdown(f"### 📄 {meta['label']}")
        context = st.text_area(f"Enter context for {meta['label']}:", key=f"ctx_{placeholder}")

        if st.button(f"Generate {meta['label']}", key=f"btn_{placeholder}"):
            result = f"""[Generated GPT Section for {meta['label']}]

{context}"""

            st.session_state["gpt_sections"][placeholder] = result

        if placeholder in st.session_state["gpt_sections"]:
            st.text_area(
                f"🧠 Generated {meta['label']} Output",
                st.session_state["gpt_sections"][placeholder],
                height=200,
                key=f"out_{placeholder}"
            )

# --- Venue & Jurisdiction Generator ---
st.divider()
with st.expander("📍 Venue & Jurisdiction Generator (optional override)"):
    venue_zip = st.text_input("Enter ZIP code of the accident location")
    defendant_county = st.text_input("Enter county where Defendant resides (if known)")
    defendant_principal_office = st.text_input("Enter county of Defendant's principal office (if applicable)")

    def generate_venue_narrative(accident_county, def_county=None, office_county=None):
        venue_bases = []
        if accident_county:
            venue_bases.append(f"under CPRC §15.002(a)(1) because a substantial part of the events giving rise to this lawsuit occurred in {accident_county} County")
        if def_county:
            venue_bases.append(f"under CPRC §15.002(a)(2) because the Defendant resides in {def_county} County")
        if office_county:
            venue_bases.append(f"under CPRC §15.002(a)(3) because the Defendant’s principal office is located in {office_county} County")
        return f"Venue is proper in {accident_county} County, Texas, and also potentially " + "; ".join(venue_bases) + "."

    if st.button("Generate Venue Narrative"):
        accident_county = "Harris" if venue_zip == "77002" else "Unknown"
        venue_narrative = generate_venue_narrative(
            accident_county,
            defendant_county,
            defendant_principal_office
        )
        st.text_area("Generated Venue & Jurisdiction", venue_narrative, height=200)

# --- Input Fields ---
st.divider()
st.subheader("📝 Input Client Information Manually")
# --- Template Placeholder Schemas ---
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

# Optional aliases for internal consistency
PLACEHOLDER_ALIAS_MAP = {
    "[CLIENT_NAME]": "[PLAINTIFFS_NAME]",
    "[CLIENT_DOB]": "[PLAINTIFFS_DOB]",
    "[CLIENT_PHONE]": "[PLAINTIFFS_PHONE]"
}

# Handles Word merge-code style placeholders
CUSTOM_ALIAS_MAP = {
    "«PlaintiffName»": "[CLIENT_NAME]",
    "«PlaintiffLastName»": "[CLIENT_NAME]",
    "«PlaintiffAddress»": "[CLIENT_ADDRESS]",
    "«PlaintiffCounty»": "[CLIENT_COUNTY]",
    "«DefendantName»": "[DEFENDANT_1_NAME]",
    "«DefendantLastName»": "[DEFENDANT_1_NAME]",
    "«DefendantAddress»": "[DEFENDANT_1_ADDRESS]"
}

# --- Generate Replacements from Webhook Data ---
def generate_replacements_from_webhook(webhook_data):
    replacements = {}

    for section_fields in PLACEHOLDER_SCHEMA.values():
        for placeholder, label in section_fields.items():
            if isinstance(label, str):
                zapier_key = label.lower().replace(" ", "_")
                value = webhook_data.get(zapier_key, "")
                replacements[placeholder] = value

                if placeholder in PLACEHOLDER_ALIAS_MAP:
                    alias = PLACEHOLDER_ALIAS_MAP[placeholder]
                    replacements[alias] = value

    for custom_token, alias_placeholder in CUSTOM_ALIAS_MAP.items():
        if alias_placeholder in replacements:
            replacements[custom_token] = replacements[alias_placeholder]
            if "LastName" in custom_token:
                name_val = replacements[alias_placeholder]
                if name_val:
                    replacements[custom_token] = name_val.split()[-1]

    return replacements

# --- Replace Placeholders in .docx Template ---
def fill_placeholders(doc: Document, replacements: dict):
    for p in doc.paragraphs:
        for key, val in replacements.items():
            if key in p.text:
                p.text = p.text.replace(key, val)
    return doc

# --- Scan Utility to List Placeholders in All Templates ---
def extract_placeholders(docx_path):
    placeholders = set()
    doc = Document(docx_path)
    for p in doc.paragraphs:
        tokens = re.findall(r"[\[][^\]]+[\]]|[«][^\u00bb]+[»]", p.text)
        placeholders.update(tokens)
    return placeholders

def scan_all_templates(template_dir="templates"):
    all_placeholders = {}
    for filename in os.listdir(template_dir):
        if filename.endswith(".docx"):
            path = os.path.join(template_dir, filename)
            tokens = extract_placeholders(path)
            all_placeholders[filename] = sorted(tokens)
    return all_placeholders

# --- Final Document Generation (to use in Streamlit app) ---
def generate_final_document(template_key, webhook_data):
    template_path = os.path.join("templates", f"{template_key}.docx")
    doc = Document(template_path)
    replacements = generate_replacements_from_webhook(webhook_data)
    buffer = generate_final_document(selected_template_key, st.session_state.get("webhook_data", {}))
    buffer = BytesIO()
    filled_doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- Entry point for debugging ---
if __name__ == "__main__":
    print("\n📄 Detected Placeholders by Template:\n")
    result = scan_all_templates("templates")
    for file, tokens in result.items():
        print(f"🗂️  {file}:")
        for t in tokens:
            print(f"  - {t}")
        print()


# --- Template Loading and Document Generation ---
def load_template(template_name):
    
 # --- Final Document Generation and Download ---
if selected_template_key:
    webhook_data = st.session_state.get("webhook_data", {})
    buffer = generate_final_document(selected_template_key, webhook_data)

    if st.button("📄 Preview Document Text"):
        preview_doc = Document(buffer)
        preview_text = "\n".join(p.text for p in preview_doc.paragraphs)
        st.text_area("Document Preview", preview_text, height=400)

    st.download_button(
        label="📥 Download Final Document",
        data=buffer.getvalue(),
        file_name=f"{selected_template_key}_final.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
   
    path = os.path.join("templates", f"{template_name}.docx")
    if not os.path.exists(path):
        st.error(f"❌ Template not found: {template_name}.docx")
        return None
    return Document(path)


if selected_template_key:
    buffer = generate_final_document(
    selected_template_key,
    st.session_state.get("webhook_data", {})
)
        if st.button("📄 Preview Document Text"):
            preview = "\n".join(p.text for p in filled_doc.paragraphs)

            st.text_area("Document Preview", preview, height=400)

        buffer = BytesIO()
        filled_doc.save(buffer)
        st.download_button(
            label="📥 Download Final Document",
            data=buffer.getvalue(),
            file_name=f"{selected_template_key}_final.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
# (To be added next message due to size constraints)




























