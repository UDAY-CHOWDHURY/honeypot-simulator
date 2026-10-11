import json
import time
import logging
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from typing import Dict, Any, List
import os
from IPython.display import clear_output
from collections import Counter
logging.basicConfig(level=logging.INFO)

# ==========================================================
# ------------------- MITRE MAPPER --------------------------
# ==========================================================
def clean_harmful(value):
    return 1 if str(value).lower() in ["1", "true"] else 0
class MitreMapper:
    """Maps predicted actions to MITRE ATT&CK techniques."""

    MITRE_MAP = {
        "attempted_file_access": {
            "technique_id": "T1083",
            "technique": "File and Directory Discovery",
            "tactic": "Discovery",
            "description": "Adversaries may enumerate files/directories to identify information."
        },
        "port_scan": {
            "technique_id": "T1046",
            "technique": "Network Service Scanning",
            "tactic": "Discovery",
            "description": "Scanning target ports to identify active services."
        },
        "brute_force": {
            "technique_id": "T1110",
            "technique": "Brute Force",
            "tactic": "Credential Access",
            "description": "Adversaries attempt to guess passwords/users repeatedly."
        },
        "default": {
            "technique_id": "NA",
            "technique": "Unknown",
            "tactic": "Unknown",
            "description": "No MITRE mapping available."
        }
    }

    @staticmethod
    def map_action(action: str):
        return MitreMapper.MITRE_MAP.get(action, MitreMapper.MITRE_MAP["default"])


# ==========================================================
# ------------------ SCHEMA MANAGER ------------------------
# ==========================================================

class SchemaManager:
    def __init__(self):
        self.columns = set()

    def update_schema(self, new_record: Dict[str, Any]):
        for key in new_record.keys():
            if key not in self.columns:
                logging.info(f"[Schema] New field detected: {key}")
                self.columns.add(key)

    def apply_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        # Ensure consistent column order and presence
        for col in self.columns:
            if col not in df.columns:
                df[col] = None
        # Return columns in sorted deterministic order (optional)
        ordered = list(self.columns)
        return df[ordered]


# ==========================================================
# ------------------ LOG INGESTOR --------------------------
# ==========================================================

class LogIngestor:
    def __init__(self, filepath: str, schema_manager: SchemaManager):
        self.filepath = filepath
        self.schema = schema_manager
        self.data: List[Dict[str, Any]] = []
        self.last_size = 0

    def poll(self):
        if not os.path.exists(self.filepath):
            return []

        new_records = []
        size = os.path.getsize(self.filepath)

        # File truncated or rotated -> reset pointer and keep data
        if size < self.last_size:
            logging.info("[Ingestor] File size decreased (rotated/truncated) — resetting pointer.")
            self.last_size = 0

        with open(self.filepath, "r") as f:
            f.seek(self.last_size)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    # normalize keys (optional)
                    # ensure expected keys exist
                    self.schema.update_schema(r)
                    self.data.append(r)
                    new_records.append(r)
                except json.JSONDecodeError:
                    logging.warning("[Ingestor] Skipping invalid JSON line.")
                except Exception as e:
                    logging.exception(f"[Ingestor] Unexpected error parsing line: {e}")

        self.last_size = size
        return new_records

    def get_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self.data)
        if df.empty:
            return df
        return self.schema.apply_schema(df)


# ==========================================================
# -------------------- ML MODEL ----------------------------
# ==========================================================

class MLModel:
    def __init__(self):
        # RandomForest used as before
        self.model = RandomForestClassifier(n_estimators=200)
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.trained = False
        self.feature_names = None
        # severity mapping (string->numeric). You can adjust mapping if needed.
        self.severity_map = {"low": 1, "medium": 2, "high": 3}

    def _encode_severity_series(self, s: pd.Series) -> pd.Series:
        # Map severity strings to numeric; unknowns -> 0
        return s.astype(str).str.lower().map(self.severity_map).fillna(0).astype(int)

    def preprocess(self, df: pd.DataFrame, is_training=True) -> pd.DataFrame:
        df = df.copy()

        # -----------------------------
        # Handle severity (string -> numeric)
        # -----------------------------
        if "severity" in df.columns:
            df["severity_num"] = self._encode_severity_series(df["severity"])

        # -----------------------------
        # Handle harmful column (0/1)
        # -----------------------------
        if "harmful" in df.columns:
            df["harmful_num"] = df["harmful"].apply(clean_harmful)
        else:
            df["harmful_num"] = 0

        # -----------------------------
        # Label encode object columns (command, ip, etc.)
        # -----------------------------
        for col in df.columns:
            if df[col].dtype == "object":
                if col not in self.label_encoders:
                    if is_training:
                        le = LabelEncoder()
                        unique_vals = df[col].astype(str).fillna("None").unique().tolist()
                        if "None" not in unique_vals:
                            unique_vals.append("None")
                        le.fit(unique_vals)
                        self.label_encoders[col] = le
                        df[col] = le.transform(df[col].astype(str).fillna("None"))
                else:
                    le = self.label_encoders[col]
                    df[col] = df[col].astype(str).apply(lambda x: x if x in le.classes_ else "None")
                    df[col] = le.transform(df[col].astype(str))

        # -----------------------------
        # Fill NaNs for numeric columns
        # -----------------------------
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                df[c] = df[c].fillna(0)

        return df


    def train(self, df: pd.DataFrame, target_col="action"):
        # If the target isn't present, do nothing (preserve prior behaviour)
        if target_col not in df.columns:
            logging.info(f"[ML] Target column '{target_col}' not found; skipping training.")
            return

        # Remove rows with missing target
        df = df.dropna(subset=[target_col])
        if df.empty:
            logging.info("[ML] No labeled rows available for training after dropping NA.")
            return

        X = df.drop(columns=[target_col])
        y = df[target_col]

        X = self.preprocess(X, is_training=True)

        # prefer severity_num in features if severity exists
        # Save feature order
        self.feature_names = X.columns.tolist()

        if len(X) < 5:
            logging.info("[ML] Not enough rows to train (need >=5).")
            return

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        self.trained = True
        logging.info("[ML] Model trained successfully.")

    def predict(self, record: Dict[str, Any]):
        if not self.trained:
            return "Model not trained"

        # Build processed record using current feature_names
        processed = {}
        for f in self.feature_names:
            if f == "severity_num":
                # read severity from record and map
                processed[f] = self.severity_map.get(str(record.get("severity", "")).lower(), 0)
            else:
                processed[f] = record.get(f, None)

        df_pred = pd.DataFrame([processed])
        X = self.preprocess(df_pred, is_training=False)
        # keep feature order
        X = X[self.feature_names]
        try:
            return self.model.predict(X)[0]
        except Exception as e:
            logging.exception(f"[ML] Prediction error: {e}")
            return "prediction_error"


# ==========================================================
# -------------------- GRAPH MANAGER -----------------------
# ==========================================================

class GraphManager:
    def __init__(self):
        plt.style.use("ggplot")

    def plot(self, df: pd.DataFrame):
        if df.empty:
            return

        clear_output(wait=True)

        d = df.copy()

        # Ensure 'command' is string type
        d["command"] = d["command"].astype(str)

        # Prepare harmful numeric column for coloring and plotting
        if "harmful" in d.columns:
            d["harmful_num"] = d["harmful"].apply(
                lambda x: 1 if str(x).lower() in ["1", "true", "yes"] else 0
            )
        else:
            d["harmful_num"] = 0

        # Add severity numeric column if missing
        if "severity" in d.columns and "severity_num" not in d.columns:
            severity_map = {"low": 1, "medium": 2, "high": 3}
            d["severity_num"] = d["severity"].astype(str).str.lower().map(severity_map).fillna(0).astype(int)

        # Remove duplicate log entries (all columns) to avoid inflated counts
        d = d.drop_duplicates()

        fig = plt.figure(figsize=(14, 9))

        # 1. Scatter plot
        ax1 = fig.add_subplot(2, 1, 1)
        colors = d["harmful_num"].map({1: "blue", 0: "lightgray"})
        sizes = d["harmful_num"].map({1: 250, 0: 60})
        ax1.scatter(d["command"], d["severity_num"], s=sizes, c=colors, alpha=0.7)
        ax1.set_title("Command vs Severity (Blue = Harmful)")
        ax1.set_xlabel("Command")
        ax1.set_ylabel("Severity (1=low, 2=medium, 3=high)")
        ax1.set_xticks(range(len(d["command"].unique())))
        ax1.set_xticklabels(d["command"].unique(), rotation=45, ha="right", fontsize=9)
        ax1.legend([plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10),
                    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgray', markersize=10)],
                ['Harmful', 'Not Harmful'])

        # 2. Stacked bar chart for command frequency including all commands
        ax2 = fig.add_subplot(2, 1, 2)

        # Count command occurrences grouped by harmful status from deduplicated data
        harm_counts = pd.crosstab(d["command"], d["harmful_num"])

        # Ensure columns for both harmful and non-harmful exist
        for col in [0, 1]:
            if col not in harm_counts.columns:
                harm_counts[col] = 0

        # Sort index to have commands in a consistent order
        harm_counts = harm_counts.sort_index()

        harm_counts.plot(kind="bar", stacked=True, ax=ax2, color=["lightgray", "blue"])
        ax2.set_title("Command Frequency (From Log File)")
        ax2.set_xlabel("Command")
        ax2.set_ylabel("Count")
        ax2.legend(["Not Harmful (0)", "Harmful (1)"])

        plt.tight_layout()
        plt.show()


# ==========================================================
# ---------------- REAL-TIME CONTROLLER ---------------------
# ==========================================================

class RealTimeController:
    def __init__(self, log_path: str):
        self.schema = SchemaManager()
        self.ingestor = LogIngestor(log_path, self.schema)
        self.ml = MLModel()
        self.graphs = GraphManager()
        self.running = False

    def start(self, interval=2.0):
        self.running = True
        logging.info("[System] Real-time monitor started.")

        def clean_harmful(val):
            # Convert any boolean/string/int to 0/1
            if str(val).lower() in ["1", "true", "yes"]:
                return 1
            else:
                return 0

        try:
            while self.running:
                new_records = self.ingestor.poll()

                if new_records:
                    df = self.ingestor.get_df()

                    # -----------------------------
                    # Clean severity and harmful fields
                    # -----------------------------
                    if "severity" in df.columns:
                        df["severity"] = df["severity"].astype(str).str.lower()

                    if "harmful" in df.columns:
                        df["harmful"] = df["harmful"].apply(clean_harmful)
                    else:
                        df["harmful"] = 0  # default if missing

                    # Train ML if action label exists and model not trained
                    if (not self.ml.trained) and ("action" in df.columns):
                        self.ml.train(df, target_col="action")

                    # Plot the graphs based on harmful/command/severity
                    self.graphs.plot(df)

                    # If the ML model is trained with 'action', predict each new record
                    if self.ml.trained:
                        for rec in new_records:
                            pred = self.ml.predict(rec)
                            mitre = MitreMapper.map_action(pred)

                            print("\n=== LIVE ATTACK DETECTED ===")
                            print(f"Predicted Action: {pred}")
                            print(f"MITRE Technique ID: {mitre['technique_id']}")
                            print(f"Technique: {mitre['technique']}")
                            print(f"Tactic: {mitre['tactic']}")
                            print(f"Description: {mitre['description']}")
                            print("============================\n")
                    else:
                        # Quick summary alerts if model not trained
                        for rec in new_records:
                            if rec.get("harmful") == 1:
                                print("\n=== LIVE HARMFUL COMMAND ===")
                                print(f"Command: {rec.get('command')}")
                                print(f"Severity: {rec.get('severity')}")
                                print(f"Raw: {rec}")
                                print("============================\n")

                time.sleep(interval)
        except KeyboardInterrupt:
            logging.info("[System] Interrupted by user, stopping monitor.")
        except Exception as e:
            logging.exception(f"[System] Unexpected error in loop: {e}")
        finally:
            self.stop()


    def stop(self):
        self.running = False
        logging.info("[System] Monitor stopped.")


# ==========================================================
# ------------------- SIMULATION ENGINE ---------------------
# ==========================================================

def simulate_attack_stream(log_path: str, interval=3):
    # NOTE: We include 'severity' and 'harmful' fields as per Option A
    sample_events = [
        {
            "timestamp": "2025-11-14T06:15:03.823118Z",
            "ip": "127.0.0.1",
            "packet_size": 1011,
            "command": "help",
            "harmful": 0,
            "severity": "low"
        },
        {
            "timestamp": "2025-11-14T06:16:45.258371Z",
            "ip": "127.0.0.1",
            "packet_size": 762,
            "command": "erase",
            "harmful": 1,
            "severity": "low"
        },
        {
            "timestamp": "2025-11-14T06:18:13.536409Z",
            "ip": "127.0.0.1",
            "packet_size": 935,
            "command": "chmod",
            "harmful": 1,
            "severity": "medium"
        }]

    # continuously append one event at a time (round-robin)
    idx = 0
    while True:
        try:
            with open(log_path, "a") as f:
                ev = sample_events[idx % len(sample_events)]
                f.write(json.dumps(ev) + "\n")
            idx += 1
            time.sleep(interval)
        except Exception as e:
            logging.exception(f"[Simulator] Error writing event: {e}")
            time.sleep(interval)


# ===========================
# Run everything (entrypoint)
# ===========================

if __name__ == "__main__":
    LOG_PATH = "attack_logs.json"
    # ensure file exists
    open(LOG_PATH, "a").close()

    # start simulator in background (daemon)
    import threading
    t = threading.Thread(target=simulate_attack_stream, args=(LOG_PATH, 2), daemon=True)
    t.start()

    # create and start controller
    controller = RealTimeController(LOG_PATH)
    controller.start(interval=2)