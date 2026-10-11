import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import json

# ===========================
# 1. Load JSON Data
# ===========================
DATA_PATH = Path("backend/logs/attack_activity.json")

if not DATA_PATH.exists():
    raise FileNotFoundError(f"❌ File not found: {DATA_PATH}\nPlace your JSON file there.")

# Load JSON file (supports both list-style and line-delimited JSON)
try:
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
except json.JSONDecodeError:
    data = [json.loads(line) for line in open(DATA_PATH, 'r') if line.strip()]

df = pd.DataFrame(data)
print("✅ Dataset loaded successfully from:", DATA_PATH)
print(f"Shape: {df.shape}")
print("Columns:", df.columns.tolist())
print(df.head())

# ===========================
# 2. Feature Engineering
# ===========================
required_cols = ['packet_size', 'command', 'target', 'hour', 'harmful', 'destination_ip']
for col in required_cols:
    if col not in df.columns:
        if col in ['packet_size', 'hour']:
            df[col] = 0
        else:
            df[col] = "unknown"

# Map actions to MITRE ATT&CK classifications
mitre_map = {
    "failed_login": {"label": "brute_force", "tactic": "Credential Access", "technique": "Brute Force"},
    "port_scan": {"label": "recon", "tactic": "Reconnaissance", "technique": "Port Scanning"},
    "data_exfiltration": {"label": "exfiltration", "tactic": "Exfiltration", "technique": "Exfiltration Over Network"},
    "malware_upload": {"label": "malware_upload", "tactic": "Execution", "technique": "Malware"},
}

# Default unknown action
df["mitre_tactic"] = df["action"].apply(lambda x: mitre_map.get(x, {"tactic": "Normal"})["tactic"])
df["mitre_technique"] = df["action"].apply(lambda x: mitre_map.get(x, {"technique": "Normal"})["technique"])
df["label"] = df["action"].apply(lambda x: mitre_map.get(x, {"label": "normal"})["label"])

# Encode categorical features
protocol_map = {p: i for i, p in enumerate(df['protocol'].unique())}
df['protocol_encoded'] = df['protocol'].map(protocol_map)
df['target_type'] = df['target'].apply(lambda x: 1 if isinstance(x, str) and "confidential" in x else 0)

features = ['packet_size', 'protocol_encoded', 'hour', 'target_type']
X = df[features]

# Use MITRE tactic as target label
y = df['mitre_tactic']
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# ===========================
# 3. Train/Test Split & Model
# ===========================
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.3, random_state=42)

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('rf', RandomForestClassifier(n_estimators=150, random_state=42))
])
pipe.fit(X_train, y_train)
y_pred = pipe.predict(X_test)

# ===========================
# 4. Classification Report
# ===========================
print("\n📊 Classification Report (MITRE Tactic):\n")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# ===========================
# 5. Visualizations
# ===========================

# 1️⃣ MITRE Tactic Distribution
plt.figure(figsize=(8,5))
sns.countplot(x='mitre_tactic', data=df, palette='Set2')
plt.title("Attack Counts by MITRE Tactic")
plt.xlabel("MITRE Tactic")
plt.ylabel("Count")
plt.xticks(rotation=30)
plt.show()

# 2️⃣ Feature Importance
rf_model = pipe.named_steps['rf']
importances = rf_model.feature_importances_
feature_names = X.columns

plt.figure(figsize=(8,4))
sns.barplot(x=importances, y=feature_names, palette="viridis")
plt.title("Feature Importance in Attack Classification (MITRE)")
plt.xlabel("Importance Score")
plt.ylabel("Feature")
plt.show()

# 3️⃣ Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6,4))
sns.heatmap(cm, annot=True, cmap="Blues", fmt='g',
            xticklabels=le.classes_,
            yticklabels=le.classes_)
plt.title("Confusion Matrix (MITRE Tactic)")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

# 4️⃣ Optional: MITRE Technique Distribution
plt.figure(figsize=(10,5))
sns.countplot(x='mitre_technique', data=df, palette='Set3')
plt.title("Attack Counts by MITRE Technique")
plt.xticks(rotation=45)
plt.show()
