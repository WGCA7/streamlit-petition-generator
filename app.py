import streamlit as st
from docx import Document
import os
from io import BytesIO
import re

# --- Placeholder Schema ---
PLACEHOLDER_SCHEMA = {
    "Client Info": {
        "[CLIENT_NAME]": "Client Name",
        "[CLIENT_DOB]": "Date of Birth",
        "[CLIENT_PHONE]": "Phone Number"
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

# --- Utility Functions ---

def load_template(template_name):
    path = os.path.join("templates", f"{template_name}.docx")
    if not os.path.exists(path):
        st.error(f"❌ Template not found: {template_name}.docx")
        return None
    return Document(path)

def fill_placeholders(doc, replacements):
    for p in doc.paragraphs:
        for key, val in replacements.items():
            if key in p.text:
                p.text = p.text.replace(key, val)
    return doc

def generate_gpt_section(prompt, context):
    return f"[Generated GPT Section for: {prompt}\n\n{context}]"

def download_docx(doc, filename):
    buffer = BytesIO()
    doc.save(buffer)
    st.download_button(
        label="📥 Download Final Document",
        data=buffer.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

def extract_placeholders(doc):
    found = set()
    for p in doc.paragraphs:
        found.update(re.findall(r"\[[A-Z0-9_]+\]", p.text))
    return found

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

# --- Streamlit App UI ---

st.title("📄 Legal Document Automation")

selected_template_key = None

selected_doc_category = st.selectbox(
    "Choose Document Category:",
    ["Petitions", "Discovery", "Demand Letters", "Insurance", "Medical"]
)

if selected_doc_category == "Petitions":
    selected_petition_doc = st.selectbox("Select Petition Template:", list(petition_doc_map.keys()))
    selected_template_key = petition_doc_map[selected_petition_doc]

elif selected_doc_category == "Discovery":
    discovery_type = st.radio(
        "Select Discovery Task:",
        ["Documents to Request", "Answering Opposing Counsel Requests"]
    )
    if discovery_type == "Documents to Request":
        selected_discovery_doc = st.selectbox("Select Document to Request:", list(requests_doc_map.keys()))
        selected_template_key = requests_doc_map[selected_discovery_doc]
    elif discovery_type == "Answering Opposing Counsel Requests":
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

# --- Load and Process Template ---
if selected_template_key:
    doc = load_template(selected_template_key)

    if doc:
        st.success(f"📝 Loaded: `{selected_template_key}.docx`")

        # --- Placeholder Form Using Expanders ---
        st.subheader("🔁 Fill Placeholders")
        replacements = {}

        for section, fields in PLACEHOLDER_SCHEMA.items():
            with st.expander(f"📂 {section}"):
                show_extra = True
                if section == "Defendant Info":
                    show_extra = st.checkbox("Include Second Defendant?", key="show_def2")
                elif section == "Plaintiff Info":
                    show_extra = st.checkbox("Include Second Plaintiff?", key="show_plaintiff2")
                elif section == "Witness Info":
                    show_extra = st.checkbox("Include Witness Details?", key="show_witnesses")
                elif section == "Medical Provider Info":
                    show_extra = st.checkbox("Include Medical Providers?", key="show_medical_providers")

                for placeholder, label in fields.items():
                    if (
                        ("DEFENDANT_2" in placeholder and not st.session_state.get("show_def2", False)) or
                        ("PLAINTIFF_2" in placeholder and not st.session_state.get("show_plaintiff2", False)) or
                        ("WITNESS_" in placeholder and not st.session_state.get("show_witnesses", False)) or
                        ("MEDICAL_PROVIDER_" in placeholder and not st.session_state.get("show_medical_providers", False))
                    ):
                        continue
                    value = st.text_input(label, key=placeholder)
                    replacements[placeholder] = value

        # --- GPT-style Section Generation ---
        if st.checkbox("✍️ Add Factual Background via GPT"):
            case_facts = st.text_area("Enter case facts for GPT to expand:")
            if st.button("Generate Factual Background"):
                gpt_background = generate_gpt_section("Draft a factual background section:", case_facts)
                st.text_area("Generated Background", gpt_background, height=200)
                replacements["[FACTUAL_BACKGROUND]"] = gpt_background

        # --- Finalize Document ---
        if st.button("🔨 Generate Final Document"):
            filled_doc = fill_placeholders(doc, replacements)
            st.success("✅ Document filled with placeholder values.")

            if st.button("📄 Preview Document Text"):
                preview = "\n".join(p.text for p in filled_doc.paragraphs)
                st.text_area("Document Preview", preview, height=400)

            download_docx(filled_doc, f"{selected_template_key}_final.docx")














