import json
import time
import os
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import clear_output
from typing import Dict, Any, List
# ============================================================
# --------------- MACHINE LEARNING (RISK MODEL) --------------
# ============================================================
from matplotlib.animation import FuncAnimation
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading

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
# Extracted Severity Logic (Inserted)
# -------------------------
def show_recommendations_window(recommendations_list):
    def run_window():
        root = tk.Tk()
        root.title("ML Recommendations")
        root.overrideredirect(True) 
        root.geometry("900x500")  # slightly larger window
        root.resizable(True, True)
         
        # ---------- Header Label ----------
        header = tk.Label(root, text="Immediate Precautions Required", font=("Arial", 16, "bold"),  fg="#0a0a0a")
        header.pack(pady=5)
        border = tk.Frame(root, bg="black", highlightthickness=0)
        border.pack(fill="both", expand=True)
        titlebar = tk.Frame(border, bg="black", height=30)
        titlebar.pack(fill="x")
        # ---------- Scrolled Text ----------
        st = ScrolledText(root, wrap=tk.WORD, font=("Consolas", 11), bg="#0c0c0c", fg="#f0f1f3")
        st.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        close_btn = tk.Button(titlebar, text="✕", bg="black", fg="white",
                            border=0, command=root.destroy)
        close_btn.pack(side="right", padx=10)
        # ---------- Insert Recommendations ----------
        for rec in recommendations_list:
            st.insert(tk.END, f"{rec}\n")
        st.config(state=tk.DISABLED)  # make read-only

        # ---------- Optional: Color formatting ----------
        # Example: highlight "High Risk" in red if present
        st.tag_configure("high_risk", foreground="red", font=("Consolas", 11, "bold"))
        for i, rec in enumerate(recommendations_list):
            if "High Risk" in rec:
                st.tag_add("high_risk", f"{i+1}.0", f"{i+1}.end")

        root.mainloop()

    # Run the recommendations window in a separate thread (non-blocking)
    t = threading.Thread(target=run_window, daemon=True)
    t.start()
def train_ml_model(df):
    """Train a RandomForest model using severity, harmful, command, packet size."""

    # Encode command
    le_cmd = LabelEncoder()
    df["cmd_enc"] = le_cmd.fit_transform(df["command_lc"])#Converts command strings to numbers

    # Feature Matrix
    X = df[["severity_num", "harmful_norm", "packet_size", "cmd_enc"]].fillna(0)

    # ---------- Risk Label Logic ----------
    
    # 0 = Safe
    # 1 = Suspicious
    # 2 = Dangerous
    y = []
    for _, row in df.iterrows():
        if row["harmful_norm"] and row["severity_num"] == 3:
            y.append(2)  # danger
        elif row["harmful_norm"] or row["severity_num"] >= 2:
            y.append(1)  # suspicious
        else:
            y.append(0)  # safe
    y = np.array(y)

    model = RandomForestClassifier(n_estimators=80)#Uses 80 decision trees
    model.fit(X, y)

    return model, le_cmd


# ============================================================
# --------------- RECOMMENDATION ENGINE ----------------------
# ============================================================

def recommend_action(row, prediction):
    """Return human-readable security advice"""
    cmd = row["command_lc"]
    sev = row["severity_num"]
    harmful = row["harmful_norm"]
    mitre = row["mitre_label"]

    # ---------------- ML-Based Risk ----------------
    if prediction == 2:
        return f"⚠️ HIGH RISK – Block command '{cmd}', isolate system, check MITRE: {mitre}"
    elif prediction == 1:
        return f"🔶 Medium Risk – Monitor '{cmd}', verify user identity, validate logs ({mitre})"
    else:
        return f"🟢 Low Risk – '{cmd}' appears normal, continue monitoring"
# -------------------------
# Config / Mappings
# -------------------------
def encode_severity(sev):
    """Convert severity string -> numeric.
    low=1, medium=2, high=3, unknown=0
    """
    sev = str(sev).lower().strip()
    return SEVERITY_TO_NUM.get(sev, 0)

def encode_severity_series(series):
    return (
        series.astype(str)
              .str.lower()
              .map(SEVERITY_TO_NUM)
              .fillna(0)
              .astype(int)
    )


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

    # -------- UPDATED SEVERITY HANDLING (Extracted Logic) --------
    sev_raw = x.get("severity", "low")
    x["severity_norm"] = str(sev_raw).lower()
    x["severity_num"] = encode_severity(sev_raw)
    # -------------------------------------------------------------

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
def plot_graphs(processed, interval=30):
    

    df = pd.DataFrame(processed)

    # ---------------- Prepare Data ----------------
    # Graph 1
    c = Counter(df["command_lc"])
    g1_labels = sorted(c.keys())
    g1_vals = np.array([c[k] for k in g1_labels])

    # Graph 2
    cmds_unique = sorted(df["command_lc"].unique())
    harm = np.array([df[df["command_lc"] == cmd]["harmful_norm"].sum()
                     for cmd in cmds_unique])
    nonharm = np.array([len(df[df["command_lc"] == cmd]) -
                        df[df["command_lc"] == cmd]["harmful_norm"].sum()
                        for cmd in cmds_unique])

    # Graph 3
    avg_sev = np.array([
        df[df["command_lc"] == cmd]["severity_num"].mean()
        for cmd in cmds_unique
    ])

    # ---------------- Create Figure ----------------
    fig, axs = plt.subplots(1, 3, figsize=(20, 5))

    # ---- GRAPH 1 ----
    x1 = np.arange(len(g1_labels))
    bars1 = axs[0].bar(x1, np.zeros(len(g1_vals)), color="tab:green")
    axs[0].set_facecolor("black")
    axs[0].figure.set_facecolor("black")
    axs[0].set_xticks(x1)
    axs[0].set_xticklabels(g1_labels, rotation=45,color="white")
    axs[0].tick_params(axis='y', colors='white')
    axs[0].tick_params(axis='x', colors='white')
    axs[0].set_ylim(0, max(g1_vals) * 1.2)
    axs[0].set_title("Frequency",color="white")
    axs[0].set_xlabel("Commands",color="white")
    axs[0].set_ylabel("Count",color="white")
    # ---- GRAPH 2 ----
    x2 = np.arange(len(cmds_unique))
    w = 0.35
    bars2h = axs[1].bar(x2 , np.zeros(len(harm)),  color="tab:red")
    bars2n = axs[1].bar(x2 , np.zeros(len(nonharm)),  color="tab:green")
    axs[1].set_facecolor("black")
    axs[1].set_xticks(x2)
    axs[1].set_xticklabels(cmds_unique, rotation=45,color="white")
    axs[1].tick_params(axis='y', colors='white')
    axs[1].tick_params(axis='x', colors='white')
    axs[1].set_ylim(0, max(harm.max(), nonharm.max()) * 1.2)
    axs[1].set_title("Harmful(red) vs Non-Harmful",color="white")
    axs[1].set_xlabel("Commands",color="white")
    axs[1].set_ylabel("Count",color="white")
    # ---- GRAPH 3 ----
    x3 = np.arange(len(cmds_unique))
    bars3 = axs[2].bar(x3, np.zeros(len(avg_sev)), color="tab:green")
    axs[2].set_facecolor("black")
    axs[2].set_xticks(x3)
    axs[2].set_xticklabels(cmds_unique, rotation=45,color="white")
    axs[2].tick_params(axis='y', colors='white')
    axs[2].tick_params(axis='x', colors='white')
    axs[2].set_ylim(0, max(avg_sev) * 1.2)
    axs[2].set_title(" Severity",color="white")
    axs[2].set_xlabel("Commands",color="white")
    axs[2].set_ylabel("Severity (low-1||medium-2||high-3)",color="white")
    plt.tight_layout()

    
    # ---------------- Animation Sequence ----------------
   
    graph_data = [
        (bars1, g1_vals),
        (list(bars2h) + list(bars2n), np.concatenate([harm, nonharm])),
        (bars3, avg_sev),
    ]

    frames_per_graph = 40
    total_frames = frames_per_graph * 3

    def animate(frame):
        graph_index = frame // frames_per_graph
        step = frame % frames_per_graph
        progress = step / (frames_per_graph - 1)

        # Make sure index stays in range
        graph_index = min(graph_index, 2)

        bars, targets = graph_data[graph_index]

        # Reset height of all bars in all graphs first
        # (so previous graphs stay completed)
        # Graph 1 stays full after completion
        for i, (bars_g, vals_g) in enumerate(graph_data):
            if i < graph_index:
                for bar, val in zip(bars_g, vals_g):
                    bar.set_height(val)
            elif i == graph_index:
                for bar, val in zip(bars_g, vals_g):
                    bar.set_height(val * progress)
            else:
                for bar in bars_g:
                    bar.set_height(0)

        return []

    anim = FuncAnimation(
        fig,
        animate,
        frames=total_frames,
        interval=interval,
        blit=False,
        repeat=False
    )

    plt.show()
    return anim
def plot_graphs1(processed):

    df = pd.DataFrame(processed)
    cmds = df["command_lc"].tolist()

    plt.figure(figsize=(20, 6))

    # -------- Graph 1: Count vs Command --------
    c = Counter(cmds)
    ordered = sorted(c.keys())
    vals = [c[k] for k in ordered]

    plt.subplot(1, 3, 1)
    plt.bar(ordered, vals)
    plt.title("Count vs Command")
    plt.xlabel("Commands")
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

    plt.subplot(1, 3, 2)
    plt.bar([i - w/2 for i in x], harm, width=w, color="blue", label="Harmful")
    plt.bar([i + w/2 for i in x], nonharm, width=w, color="orange", label="Not Harmful")

    plt.xticks(list(x), cmds_unique, rotation=45)
    plt.ylabel("Count")
    plt.xlabel("Commands")
    plt.title("Severity & Harmfulness vs Command")
    plt.legend()

    # -------- Graph 3: Severity vs Command --------
    plt.subplot(1, 3, 3)
    plt.bar(cmds_unique, avg_sev, color="green")
    plt.title("Severity vs Command (Avg Severity)")
    plt.xlabel("Commands")
    plt.ylabel("Average Severity (1=low, 2=medium, 3=high)")
    plt.ylim(0, 3.5)
    plt.xticks(rotation=45)

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
                df = pd.DataFrame(processed)

# ---------- Train ML Model ----------
                model, le_cmd = train_ml_model(df)

                # ---------- Generate Predictions ----------
                df["cmd_enc"] = le_cmd.transform(df["command_lc"])#Converts command strings to integers
                X_live = df[["severity_num", "harmful_norm", "packet_size", "cmd_enc"]].fillna(0)
                df["risk_pred"] = model.predict(X_live)

                # ---------- Generate Recommendations ----------
                df["recommendation"] = df.apply(lambda r: recommend_action(r, r["risk_pred"]), axis=1)

                recommendations_list = [
                    f"{row['timestamp']} | {row['command']} → {row['recommendation']}"
                    for i, row in df.iterrows()
                ]

# Show in a separate window
                show_recommendations_window(recommendations_list)

                print("Updated at:", datetime.now())
                print("Records:", len(processed))

                plot_graphs(processed)

            time.sleep(refresh_interval)

        except KeyboardInterrupt:
            print("\nEnded...")
            break

        except Exception as e:
            print("Error:", e)
            time.sleep(2)


# -------------------------
# RUN: Ask user for file path
# -------------------------

json_path ="C:/Users/DELL/Desktop/DOCMY/PROJECTS/HONEYPOT/honeypot/backend/simulation/logs/attack_activity.json"
run_live(json_path)