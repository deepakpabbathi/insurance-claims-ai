"""
schema.py

Contains database schema and few-shot examples
used for prompt construction.
"""
# -----------------------------
# Schema dictionary (all columns)
# -----------------------------
SCHEMA_DICT = {

"Claim Number": "Unique identifier for each insurance claim",
"Policy Number": "Insurance policy associated with the claim",
"Date of Loss": "Date when the accident or damage occurred",
"Time of Loss": "Time when the incident occurred",
"Loss Location": "Address where the loss happened",
"Claimant Name": "Person who filed the claim",

"Vehicle Make": "Brand or manufacturer of the vehicle such as Toyota, Honda, Ford, Chevrolet, BMW etc.",
"Vehicle Model": "Specific model of the vehicle",
"Vehicle Year": "Manufacturing year of the vehicle",

"Damage Description": "Type of vehicle damage reported in the claim. Possible categories include: Side collision, Front-end damage, Rear-end damage, Minor scratches, and Total loss.",

"Reported By": "Person or entity who reported the claim",

"Claim Status": "Current status of the insurance claim. Possible categories include: Open (new claim), Pending (awaiting processing), Under Investigation (claim being reviewed), and Closed (claim completed or finalized).",

"Police Report": "Indicates whether a police report was submitted for the accident (YES/NO)",
"Photos/Videos": "Indicates whether photo or video evidence of the damage was submitted (YES/NO)",

"Repair Estimate": "Indicates whether a repair estimate document was submitted (YES/NO)",
"Repair Estimate Cost": "Estimated cost of repairing vehicle damage",

"Towing Receipt": "Indicates whether a towing service receipt was submitted (YES/NO)",
"Rental Receipt": "Indicates whether a vehicle rental receipt was submitted (YES/NO)",

"Medical & Injury Documentation": "Administrative flag only (Yes/No). Indicates whether paperwork was submitted. Do NOT use this column to determine if a claim required hospitalisation.",

"Medical Reports": "Type of injury to the claimant's body. Values: Fractured arm, Whiplash, Minor cuts and bruises, Internal injuries, Concussion. This describes the INJURY TYPE only — not whether the person was hospitalised.",

"Hospital Records": "THE column that determines hospitalisation. Possible values include: Surgery required, ER visit (emergency treatment), Physiotherapy, Outpatient consultation, Overnight observation.",

"Hospital Cost": "Cost of medical treatment or hospitalization related to the injury",

"Third-Party Information": "Indicates whether another party was involved in the accident (YES/NO)",
"Third-Party Insurance": "Indicates whether the third party had insurance coverage (YES/NO)",
"Third-Party Claim Form": "Indicates whether a third-party claim form was submitted (YES/NO)",

"City": "City where the accident or loss occurred. Nearly unique per row",
"State": "State where the accident or loss occurred"
}

# -----------------------------
# Generic few-shot examples
# -----------------------------
EXAMPLES = """
Example 1
Question:
How many total claims exist in the dataset?

SQL:
SELECT COUNT(*) FROM claims;

Example 2
Question:
What is the average repair estimate cost?

SQL:
SELECT AVG("Repair Estimate Cost") FROM claims;
"""