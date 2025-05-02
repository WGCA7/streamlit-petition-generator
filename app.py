import streamlit as st
from docx import Document
import os
from io import BytesIO

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
    # Placeholder GPT logic
    return f"[Generated: {prompt} -> {context}]"

def download_docx(doc, filename):
    buffer = BytesIO()
    doc.save(buffer)
    st.download_button(
        label="📥 Download Final Document",
        data=buffer.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# --- Template Maps ---

petition_doc_map = {
    "MVA - 1 Defendant Original Petition": "mva_1_defendant_original_petition",
    "MVA - 2 Defendants Original Petition": "mva_2_defendants_original_petition",
    "Premises Liability Original Petition": "premises_liability_original_petition",
    "Wrongful Death Original Petition": "wrongful_death_original_petition",
    "Dog Bite Original Petition": "dog_bite_original_petition",
    "Medical Malpractice Original Petition": "medical_malpractice_original_petition"
}

discovery_doc_map = {
    "Plaintiff's Initial Disclosures": "initial_disclosures",
    "Plaintiff's Interrogatories": "interrogatories",
    "Plaintiff's Request for Admissions": "request_for_admissions",
    "Plaintiff's Request for Production": "request_for_production",
    "Plaintiff's Request for Disclosures": "request_for_disclosures",
    "Answer to Interrogatories": "answer_to_interrogatories",
    "Answer to Request for Admissions": "answer_to_request_for_admissions",
    "Answer to Request for Production": "answer_to_request_for_production",
    "Answer to Request for Disclosures": "answer_to_request_for_disclosures"
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

misc_templates = {
    "Medical Records Request": "medical_records_request",
    "Third Party Spoliation Letter": "third_party_spoliation_letter"
}

# --- Streamlit UI ---

st.title("Legal Document Automation")

selected_doc_category = st.selectbox(
    "Choose Document Category:",
    ["Petitions", "Discovery", "Demand Letters", "Insurance", "Medical"]
)

if selected_doc_category == "Petitions":
    selected_petition_doc = st.selectbox("Select Petition Template:", list(petition_doc_map.keys()))
    selected_template_key = petition_doc_map[selected_petition_doc]

elif selected_doc_category == "Discovery":
    selected_discovery_doc = st.selectbox(
        "Select Discovery Document:",
        list(discovery_doc_map.keys())
    )
    selected_template_key = discovery_doc_map[selected_discovery_doc]

elif selected_doc_category == "Demand Letters":
    selected_demand_doc = st.selectbox("Select Demand Letter Type:", list(demand_letters.keys()))
    selected_template_key = demand_letters[selected_demand_doc]

elif selected_doc_category == "Insurance":
    selected_insurance_doc = st.selectbox("Select Insurance Document:", list(insurance_docs.keys()))
    selected_template_key = insurance_docs[selected_insurance_doc]

elif selected_doc_category == "Medical":
    selected_medical_doc = st.selectbox("Select Medical Document:", list(medical_docs.keys()))
    selected_template_key = medical_docs[selected_medical_doc]

# Load and modify the document
doc = load_template(selected_template_key)
if doc:
    st.write(f"📝 Loaded template: `{selected_template_key}.docx`")

    st.subheader("🔁 Fill Placeholders")
    client_name = st.text_input("Client Name")
    date_of_accident = st.date_input("Date of Accident")
    attorney_name = st.text_input("Attorney Name")

    # Optional GPT section generation
    factual_background = ""
    venue_text = ""

    if st.checkbox("✍️ Generate Factual Background via GPT"):
        facts = st.text_area("Enter case facts:")
        if st.button("Generate Factual Background"):
            factual_background = generate_gpt_section("Factual Background", facts)
            st.text_area("Generated Factual Background", factual_background, height=200)

    if st.checkbox("✍️ Generate Venue & Jurisdiction via GPT"):
        venue_input = st.text_area("Describe venue and location context:")
        if st.button("Generate Venue Section"):
            venue_text = generate_gpt_section("Venue & Jurisdiction", venue_input)
            st.text_area("Generated Venue Section", venue_text, height=200)

    if st.button("Generate Final Document"):
        replacements = {
            "[CLIENT_NAME]": client_name,
            "[DATE_OF_ACCIDENT]": date_of_accident.strftime("%B %d, %Y"),
            "[ATTORNEY_NAME]": attorney_name,
            "[FACTUAL_BACKGROUND]": factual_background,
            "[VENUE]": venue_text
        }
        filled_doc = fill_placeholders(doc, replacements)
        st.success("✅ Document generated with all placeholders filled.")
        download_docx(filled_doc, f"{selected_template_key}_final.docx")











