import random

# Dummy classifier for testing purposes
def classify_event(log):
    possible_labels = ["Reconnaissance", "Execution", "Lateral Movement", "Exfiltration"]
    return random.choice(possible_labels)

# Mapping to MITRE ATT&CK techniques
MITRE_MAP = {
    "Reconnaissance": "T1595 – Active Scanning",
    "Execution": "T1059 – Command and Scripting Interpreter",
    "Lateral Movement": "T1075 – Pass the Hash",
    "Exfiltration": "T1041 – Exfiltration Over C2 Channel"
}

def map_to_mitre(label):
    return MITRE_MAP.get(label, "T0000 – Unknown Technique")
