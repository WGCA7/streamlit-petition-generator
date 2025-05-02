import streamlit as st

# --- Mapping dictionaries ---

# Petition document map
petition_doc_map = {
    "Standard Personal Injury Petition": "standard_personal_injury_petition",
    "Motor Vehicle Accident Petition": "motor_vehicle_accident_petition",
    "Premises Liability Petition": "premises_liability_petition",
    "Wrongful Death Petition": "wrongful_death_petition",
    "Dog Bite Petition": "dog_bite_petition",
    "Assault Petition": "assault_petition",
    "Medical Malpractice Petition": "medical_malpractice_petition"
}

# Discovery document map
discovery_doc_map = {
    "Plaintiff's Initial Disclosures": "initial_disclosures",
    "Plaintiff's Request for Admissions": "request_for_admissions",
    "Plaintiff's Interrogatories": "interrogatories",
    "Plaintiff's Request for Production": "request_for_production",
    "Plaintiff's Request for Disclosures": "request_for_disclosures",
    "Answer to Request for Admissions": "answer_to_request_for_admissions",
    "Answer to Interrogatories": "answer_to_interrogatories",
    "Answer to Request for Production": "answer_to_request_for_production",
    "Answer to Request for Disclosures": "answer_to_request_for_disclosures"
}

# Template generator maps
basic_templates = {
    "Letter of Representation": "letter_of_representation",
    "Letter of Protection": "letter_of_protection",
    "Medical Records Request": "medical_records_request",
    "Third Party Spoliation Letter": "third_party_spoliation_letter"
}

demand_letters = {
    "Stowers Demand Letter": "stowers_demand_letter",
    "General Demand Letter": "demand_letter",
    "Motor Vehicle Accident Demand Letter": "motor_vehicle_demand_letter",
    "Uninsured/Underinsured Motorist Demand Letter": "um_uim_demand_letter",
    "Slip and Fall Demand Letter": "slip_and_fall_demand_letter",
    "Dog Bite Demand Letter": "dog_bite_demand_letter"
}

# --- UI Starts Here ---
st.title("Legal Document Automation")

# Function Selector
selected_function = st.selectbox(
    "Choose Function:",
    ["Petition", "Template Generator"]
)

# Document Category Selector
if selected_function == "Petition":
    selected_doc_category = "Petitions"  # Locked to petitions
else:
    selected_doc_category = st.selectbox(
        "Choose Document Category:",
        ["Petitions", "Discovery"]
    )

# PETITION SECTION
if selected_function == "Petition":
    selected_petition_doc = st.selectbox(
        "Select Petition Type:",
        list(petition_doc_map.keys())
    )
    selected_template_key = petition_doc_map[selected_petition_doc]

# DISCOVERY SECTION
elif selected_doc_category == "Discovery":
    discovery_type = st.radio(
        "Select Discovery Task:",
        ["Answering Opposing Counsel Requests", "Drafting Our Requests"]
    )

    if discovery_type == "Answering Opposing Counsel Requests":
        selected_discovery_doc = st.selectbox(
            "Select Discovery Document to Answer:",
            [
                "Answer to Request for Admissions",
                "Answer to Interrogatories",
                "Answer to Request for Production",
                "Answer to Request for Disclosures"
            ]
        )
    else:
        selected_discovery_doc = st.selectbox(
            "Select Discovery Document to Draft:",
            [
                "Plaintiff's Initial Disclosures",
                "Plaintiff's Request for Admissions",
                "Plaintiff's Interrogatories",
                "Plaintiff's Request for Production",
                "Plaintiff's Request for Disclosures"
            ]
        )

    selected_template_key = discovery_doc_map[selected_discovery_doc]

# TEMPLATE GENERATOR SECTION
elif selected_function == "Template Generator":
    template_type = st.selectbox(
        "Select Template Type:",
        ["General Templates", "Demand Letters"]
    )

    if template_type == "General Templates":
        selected_template_doc = st.selectbox(
            "Select Document:",
            list(basic_templates.keys())
        )
        selected_template_key = basic_templates[selected_template_doc]

    elif template_type == "Demand Letters":
        selected_demand_doc = st.selectbox(
            "Select Demand Letter Type:",
            list(demand_letters.keys())
        )
        selected_template_key = demand_letters[selected_demand_doc]

# Load the selected template (placeholder logic)
st.write(f"\n📝 You selected template: `{selected_template_key}`")
# template = load_template(f"{selected_template_key}.docx")  # Replace this with your document logic








