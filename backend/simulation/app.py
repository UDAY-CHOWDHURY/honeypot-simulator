# backend/app.py
import os
import json
import time
import random
import threading
import requests
import redis
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sse import sse
# List of commands considered potentially harmful
HARMFUL_COMMANDS = [
    "del", "erase", "rm", "shutdown", "format", "mkfs", "net user", "curl",
    "wget", "scp", "powershell", "chmod", "chown", "dd", "nc", "ncat"
]
# Optional local llama-cpp support (will be used as a fallback if available)
try:
    from llama_cpp import Llama
except Exception:
    Llama = None

# Optional faker (you already used it)
try:
    from faker import Faker
    fake = Faker()
except Exception:
    fake = None

app = Flask(__name__)
app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")
app.config["LLAMA_MODEL_PATH"] = os.getenv("LLAMA_MODEL_PATH", "")  # optional local GGUF
app.config["OLLAMA_URL"] = os.getenv("OLLAMA_URL", "http://localhost:11434")
app.config["OLLAMA_MODEL"] = os.getenv("OLLAMA_MODEL", "llama3")     # default Ollama model name
app.config["OLLAMA_TIMEOUT"] = float(os.getenv("OLLAMA_TIMEOUT", "30"))

app.register_blueprint(sse, url_prefix='/stream')
CORS(app)

# Simulation workflows (unchanged)
workflows = [
    ["open_browser", "visit_website", "download_file"],
    ["open_editor", "write_notes", "save_file"],
    ["check_email", "open_attachment"]
]

# Redis client
r = redis.from_url(app.config["REDIS_URL"])

# Try to load a local LLAMA model (llama_cpp) as a fallback
local_llama = None
if Llama is not None and app.config["LLAMA_MODEL_PATH"]:
    model_path = os.path.expanduser(app.config["LLAMA_MODEL_PATH"])
    if os.path.exists(model_path):
        try:
            local_llama = Llama(model_path=model_path)
            app.logger.info("Loaded local model (llama_cpp) from %s", model_path)
        except Exception as e:
            app.logger.warning("Failed to init local Llama model: %s", e)
            local_llama = None
    else:
        app.logger.info("LLAMA_MODEL_PATH set but file not found at %s", model_path)
def is_harmful_command(cmd):
    cmd_lower = cmd.lower()
    return any(harmful in cmd_lower for harmful in HARMFUL_COMMANDS)
def log_trap_command(cmd):
    log_path = "backend/logs/attack_activity.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    harmful = is_harmful_command(cmd)
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "command": cmd,
        "source_ip": request.remote_addr,
        "harmful": harmful
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
def command_severity(cmd):
    """Return severity: low / medium / high"""
    cmd_lower = cmd.lower()
    if any(x in cmd_lower for x in ["del", "rm", "format", "mkfs", "dd"]):
        return "high"
    elif any(x in cmd_lower for x in ["net user", "chmod", "chown", "powershell"]):
        return "medium"
    return "low"

# Helper: Create or retrieve per-IP system profile from Redis
def get_or_create_profile(ip):
    key = f"honeypot:profile:{ip}"
    s = r.get(key)
    if s:
        return json.loads(s)
    # Build a believable fake Windows system profile
    username = fake.user_name() if fake else f"user{random.randint(100,999)}"
    hostname = f"{(fake.word().capitalize() if fake else 'Host')}-PC"
    manufacturer = random.choice(["DELL, Inc.", "HP", "Lenovo", "ASUS"])
    model = random.choice(["G15", "ThinkPad X1", "Pavilion", "ROG Strix"])
    build = f"10.0.19045.{random.randint(100, 9999)}"
    tz = random.choice(["UTC", "UTC+1", "UTC-5"])
    memory_mb = random.choice([4096, 8192, 16384])
    profile = {
        "username": username,
        "hostname": hostname,
        "os_name": "Microsoft Windows 11 HOME",
        "os_version": f"10.0.19045 N/A Build {build}",
        "manufacturer": manufacturer,
        "model": model,
        "system_type": "x64-based PC",
        "time_zone": tz,
        "installed_memory_mb": memory_mb,
        "ver_string": f"Microsoft Windows [Version {build}]"
    }
    r.setex(key, 86400, json.dumps(profile))
    return profile

# Build the system/profile prompt (unchanged)
def build_prompt(profile, command):
    return f"""
You are simulating a Windows 11 Command Prompt (cmd.exe).
Respond with the exact text output that cmd.exe would display for the given command.

System Info:
Host Name: {profile['hostname']}
User Name: {profile['username']}
OS Version: {profile['os_version']}

Rules:
- Output must look like a real Windows CMD result.
- Keep it short and realistic (1–10 lines).
- Do NOT explain or add commentary. 
- Use tabs, spacing, and uppercase where Windows usually does.
- For unknown commands, return exactly:
  '{command}' is not recognized as an internal or external command,
  operable program or batch file.
- If the command is one of these, follow the examples:
  • whoami → show the username only
  • hostname → show the hostname only
  • ver → Microsoft Windows [Version 10.0.xxxxx]
  • dir → a few sample directory lines
  • ipconfig → 1–2 adapters with IPs
  • help → list of built-in commands like Windows CMD (e.g. HELP, DIR, COPY, DEL, etc.)
  • tasklist → table of processes with PIDs and memory
  • systeminfo → multiline system info summary
  • ping <target> → show ping results to the provided target (4 replies + statistics)

Command: {command}

Output:
""".strip()








# Deterministic fallback (unchanged)
def fallback_response(profile, command):
    cmd = command.lower().strip()
    if cmd == "whoami":
        return profile["username"]
    if cmd == "hostname":
        return profile["hostname"]
    if cmd == "ver":
        return profile["ver_string"]
    if cmd == "systeminfo":
        return (
            f"Host Name:                 {profile['hostname']}\n"
            f"OS Name:                   {profile['os_name']}\n"
            f"OS Version:                {profile['os_version']}\n"
            f"System Manufacturer:       {profile['manufacturer']}\n"
            f"System Model:              {profile['model']}\n"
            f"System Type:               {profile['system_type']}\n"
            f"User Name:                 {profile['username']}\n"
            f"Time Zone:                 {profile['time_zone']}\n"
            f"Installed Physical Memory: {profile['installed_memory_mb']} MB"
        )
    return f"'{command}' is not recognized as an internal or external command,\noperable program or batch file."

# ---- Ollama integration ----
def parse_ollama_ndjson(resp_text):
    results = []
    for line in resp_text.strip().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            results.append(obj)
        except json.JSONDecodeError:
            # If any line is not valid JSON, log or ignore
            pass
    return results
 # assuming you have this imported somewhere in your app
def generate_with_ollama(prompt_text, model=None, timeout=30):
    import requests, json
    base_url = app.config.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = model or app.config.get("OLLAMA_MODEL", "llama3")
    url = f"{base_url}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt_text,
        "stream": False,  # Disable streaming for clean JSON
        "temperature": 0.3,
        "num_predict": 128
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        # Get text from Ollama response
        if isinstance(data, dict):
            text = data.get("response") or data.get("output") or data.get("text")
            if text:
                text = text.strip()
                if text not in [".", "...", "**", ""]:
                    return text

        # Fallback to raw text if JSON failed
        text = resp.text.strip()
        if text not in [".", "...", "**", ""]:
            return text

    except Exception as e:
        app.logger.warning("Ollama generation failed: %s", e)

    # Last resort: generic fallback
    return f"'{prompt_text[:10]}...' not recognized as an internal or external command."


# Main generation function tries Ollama, then local llama_cpp, then fallback
def generate_shell_output(profile, command, max_tokens=512, temperature=0.2):
    prompt = build_prompt(profile, command)
    model = app.config.get("OLLAMA_MODEL", "llama3")
    timeout = app.config.get("OLLAMA_TIMEOUT", 120)

    try:
        result = generate_with_ollama(prompt, model=model, timeout=timeout)
        if result and result not in [".", "..."]:
            return result
    except Exception as ex:
        app.logger.warning("Ollama call exception: %s", ex)

    return f"(Simulated output for '{command}')"




# --- Logging and simulation helpers (unchanged) ---
def log_trap_command(cmd):
    log_path = "backend/logs/attack_activity.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "command": cmd,
        "source_ip": request.remote_addr,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def log_simulation_action(action):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "packet_size": random.randint(300, 1500),
        "protocol": random.choice(["HTTP", "HTTPS", "FTP"]),
        "destination_ip": f"192.168.1.{random.randint(2, 254)}"
    }
    log_path = "logs/activity.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def simulate_behavior():
    with app.app_context():
        workflow = random.choice(workflows)
        for action in workflow:
            print(f"➡️ Publishing: {action}")
            sse.publish({"action": action}, type='simulation')
            log_simulation_action(action)
            time.sleep(random.uniform(1, 2))

# --- Flask routes (unchanged aside from using new generate_shell_output) ---
@app.route('/trap', methods=['POST'])
@app.route('/trap', methods=['POST'])
def trap():
    data = request.get_json()
    cmd = data.get("command", "").strip()
    
    # Determine if the command is harmful
    harmful = is_harmful_command(cmd)
    severity = command_severity(cmd)  # optional, if you want severity levels

    # Build the attacker event with command info
    attacker_event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ip": request.remote_addr,
       
        "packet_size": random.randint(400, 1200),
        
        
        "command": cmd,
        "harmful": harmful,
        "severity": severity
    }

    # Log the event to attack_activity.json
    log_path = "logs/attack_activity.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(attacker_event) + "\n")

    # Optionally push event to SSE for frontend
    sse.publish({"attacker_action": attacker_event}, type='attacker')

    # Generate fake shell output
    ip = request.remote_addr
    profile = get_or_create_profile(ip)

    if not cmd:
        return jsonify({"response": ""})

    try:
        generated = generate_shell_output(profile, cmd)
    except Exception as e:
        app.logger.error("Generation exception: %s", e)
        generated = fallback_response(profile, cmd)

    return jsonify({"response": generated})

"""
def trap():
    data = request.get_json()
    cmd = data.get("command", "").strip()
    log_trap_command(cmd)

    attacker_event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ip": request.remote_addr,
        "action": "attempted_file_access",
        "target": "/fake_files/confidential.docx",
        "packet_size": random.randint(400, 1200),
        "protocol": random.choice(["SSH", "HTTP", "Telnet"]),
        "destination_ip": f"10.0.0.{random.randint(2, 254)}"
    }

    log_path = "logs/attack_activity.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(attacker_event) + "\n")

    sse.publish({"attacker_action": attacker_event}, type='attacker')
    ip = request.remote_addr
    profile = get_or_create_profile(ip)

    if not cmd:
        return jsonify({"response": ""})

    try:
        generated = generate_shell_output(profile, cmd)
    except Exception as e:
        app.logger.error("Generation exception: %s", e)
        generated = fallback_response(profile, cmd)
    

    return jsonify({"response": generated})
"""
@app.route('/simulate', methods=['POST'])
def start_simulation():
    try:
        r.ping()
        print("✅ Redis is reachable")
    except Exception as e:
        print("❌ Redis connection failed:", e)
    thread = threading.Thread(target=simulate_behavior)
    thread.start()
    return jsonify({"status": "simulation started"})

@app.route('/')
def index():
    return "Backend is running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
