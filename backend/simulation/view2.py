import json
import time
import os
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import clear_output
from typing import Dict, Any, List

# -------------------------
# Config / Mappings
# -------------------------

SEVERITY_TO_NUM = {"low": 1, "medium": 2, "high": 3}
HARMFUL_TRUE = {"true", "True", True, "yes", "1", 1}

MITRE_MAPPING = {
    "help": "Reconnaissance",
    "erase": "Data Destruction",
    "rm": "Data Destruction",
    "del": "Data Destruction",
    "chmod": "Privilege Modification",
    "chown": "Privilege Modification",
    "whoami": "Discovery",
    "uname": "Discovery",
    "curl": "Execution / Remote File Download",
    "wget": "Execution / Remote File Download",
}

PATTERN_RULES = [
    (lambda e: e.get("packet_size", 0) > 900 and e.get("harmful") in HARMFUL_TRUE,
     "Potential Data Exfiltration (rule)"),
]

# -------------------------
# Utility
# -------------------------

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def normalize(e: Dict[str, Any]) -> Dict[str, Any]:
    x = dict(e)

    # timestamp
    ts = x.get("timestamp")
    try:
        x["timestamp_epoch"] = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
    except:
        x["timestamp_epoch"] = None

    # packet_size
    try:
        x["packet_size"] = int(x.get("packet_size"))
    except:
        x["packet_size"] = None

    # command
    cmd = str(x.get("command", "")).strip()
    x["command"] = cmd
    x["command_lc"] = cmd.lower()

    # severity
    sev = str(x.get("severity", "low")).lower()
    if sev not in SEVERITY_TO_NUM:
        sev = "low"
    x["severity_norm"] = sev
    x["severity_num"] = SEVERITY_TO_NUM[sev]

    # harmful
    harm = x.get("harmful", False)
    x["harmful_norm"] = True if harm in HARMFUL_TRUE else False

    return x


def classify_mitre(e: Dict[str, Any]) -> str:
    # Pattern rules first
    for pred, label in PATTERN_RULES:
        try:
            if pred(e):
                return label
        except:
            pass

    cmd = e.get("command_lc", "")
    if cmd in MITRE_MAPPING:
        return MITRE_MAPPING[cmd]

    return "Unknown"


def process(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for ev in events:
        ne = normalize(ev)
        ne["mitre_label"] = classify_mitre(ne)
        out.append(ne)
    return out


# -------------------------
# Plotting (Shown Live in Colab)
# -------------------------

def plot_graphs(processed):

    df = pd.DataFrame(processed)
    cmds = df["command_lc"].tolist()

    # -------- Graph 1: Count vs Command --------
    c = Counter(cmds)
    ordered = sorted(c.keys())
    vals = [c[k] for k in ordered]

    plt.figure(figsize=(15, 5))
    plt.subplot(1, 2, 1)
    plt.bar(ordered, vals)
    plt.title("Count vs Command")
    plt.xlabel("Command")
    plt.ylabel("Count")
    plt.xticks(rotation=45)

    # -------- Graph 2: Severity + Harmful --------
    cmds_unique = sorted(df["command_lc"].unique())
    avg_sev = []
    harm = []
    nonharm = []

    for cmd in cmds_unique:
        sub = df[df["command_lc"] == cmd]
        avg_sev.append(sub["severity_num"].mean())
        harm.append(sum(sub["harmful_norm"]))
        nonharm.append(len(sub) - sum(sub["harmful_norm"]))

    x = range(len(cmds_unique))
    w = 0.35

    plt.subplot(1, 2, 2)
    plt.bar([i - w/2 for i in x], harm, width=w, color="blue", label="Harmful")
    plt.bar([i + w/2 for i in x], nonharm, width=w, color="orange", label="Not Harmful")

    plt.xticks(list(x), cmds_unique, rotation=45)
    plt.ylabel("Count")
    plt.title("Severity & Harmfulness vs Command")

    plt.legend()
    plt.tight_layout()
    plt.show()


# -------------------------
# Auto-Refresh Loop
# -------------------------

def run_live(json_path: str, refresh_interval: float = 2.0):
    print(f"Watching file: {json_path}")
    print("Auto refresh enabled. Modify the JSON file to see live update.\n")

    last_modified = None

    while True:
        try:
            new_modified = os.path.getmtime(json_path)

            # File changed
            if last_modified is None or new_modified != last_modified:
                last_modified = new_modified

                clear_output(wait=True)

                events = load_jsonl(json_path)
                processed = process(events)

                print("Updated at:", datetime.now())
                print("Records:", len(processed))

                plot_graphs(processed)

            time.sleep(refresh_interval)

        except KeyboardInterrupt:
            print("\nStopped by user.")
            break

        except Exception as e:
            print("Error:", e)
            time.sleep(2)


# -------------------------
# RUN: Ask user for file path
# -------------------------

json_path = input("Enter JSONL file path in Colab: ").strip()
run_live(json_path)