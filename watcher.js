// watcher.js

const fs = require('fs');
const path = require('path');
const os = require('os');
const { exec } = require('child_process');

// === Configuration ===

// Trigger file path (Desktop/trigger.txt)
const triggerFile = path.join(os.homedir(), 'Desktop', 'trigger.txt');

// Your React project path (adjust this!)
const projectPath = path.join(__dirname); // Use __dirname if the script is inside the project

// Port the app will run on
const appURL = 'http://localhost:3000';

// Interval to check (ms)
const interval = 0.0001;

// === Watcher ===

console.log(`Watching for deletion of: ${triggerFile}`);

const watcher = setInterval(() => {
  if (!fs.existsSync(triggerFile)) {
    console.log(' Trigger file deleted. Launching honeypot...');

    // Run `npm start` inside the React project
    const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';

    const child = exec(`${npmCommand} start`, { cwd: projectPath }, (err, stdout, stderr) => {
      if (err) {
        console.error('Error launching honeypot:', err);
        return;
      }
      console.log('Honeypot launched successfully.');
    });

    // Optionally, open the browser after a short delay
    setTimeout(() => {
      let openCmd;

      if (process.platform === 'win32') openCmd = `start ${appURL}`;
      else if (process.platform === 'darwin') openCmd = `open ${appURL}`;
      else openCmd = `xdg-open ${appURL}`;

      exec(openCmd);
    }, 3000);

    // Stop checking
    clearInterval(watcher);
  }
}, interval);
// watcher.js

// watcher.js

/*const fs = require("fs");
const path = require("path");
const os = require("os");
const { exec } = require("child_process");

// ================= CONFIGURATION =================

// Path for file deletion trigger (example: Desktop/trigger.txt)
const triggerFile = path.join(os.homedir(), "Desktop", "trigger.txt");

// Path to your React honeypot project
const projectPath = path.join(__dirname); // adjust if needed

// URL where app runs
const appURL = "http://localhost:3000";

// Log file for recording detection
const logFile = path.join(__dirname, "honeypot_trigger.log");

// Path to auth log (Linux)
const AUTH_LOG = path.join(os.homedir(), "Desktop", "test_auth.log"); // or "/var/log/secure" for RHEL/CentOS

// Parameters for brute-force detection
const FAILED_THRESHOLD = 10; // number of failed attempts
const WINDOW_MS = 5 * 60 * 1000; // 5 minutes window
const COOLDOWN_MS = 30 * 60 * 1000; // 30 minutes cooldown

// Regex patterns for SSH failed login logs
const RE_FAILED_SSH = /Failed password for (?:invalid user )?\S+ from (\d+\.\d+\.\d+\.\d+)/;
const RE_FAILED_GENERIC = /rhost=(\d+\.\d+\.\d+\.\d+)/;

// Map for tracking failed attempts per IP
const failedAttempts = {};
const cooldowns = {};

// ==================================================

// Simple logging function
function log(msg) {
  const entry = `[${new Date().toISOString()}] ${msg}\n`;
  console.log(entry.trim());
  fs.appendFileSync(logFile, entry);
}

// Function to launch honeypot
function launchHoneypot(reason = "unknown", ip = "N/A") {
  log(`🔥 Honeypot Triggered by ${reason} from ${ip}`);

  const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
  const child = exec(`${npmCommand} start`, { cwd: projectPath });

  child.stdout.on("data", (data) => console.log(data.toString()));
  child.stderr.on("data", (data) => console.error(data.toString()));

  // Open in browser
  setTimeout(() => {
    let openCmd;
    if (process.platform === "win32") openCmd = `start ${appURL}`;
    else if (process.platform === "darwin") openCmd = `open ${appURL}`;
    else openCmd = `xdg-open ${appURL}`;
    exec(openCmd);
  }, 3000);
}

// ================= FILE DELETION TRIGGER =================

function watchFileDeletion() {
  log(`👁 Watching for deletion of: ${triggerFile}`);

  const watcher = setInterval(() => {
    if (!fs.existsSync(triggerFile)) {
      log("🚨 Trigger file deleted → Launching honeypot...");
      launchHoneypot("file_deletion");
      clearInterval(watcher);
    }
  }, 1000);
}

// ================= FAILED LOGIN TRIGGER =================

function watchFailedLogins() {
  if (!fs.existsSync(AUTH_LOG)) {
    log(`⚠️ Auth log not found at ${AUTH_LOG}, skipping login watcher`);
    return;
  }

  log(`👁 Monitoring failed logins from ${AUTH_LOG}`);

  const stream = fs.createReadStream(AUTH_LOG, {
    encoding: "utf8",
    flags: "r",
  });

  stream.on("data", (chunk) => {
    const lines = chunk.split("\n");
    lines.forEach((line) => processLogLine(line));
  });

  // Watch file for appends (new log entries)
  fs.watchFile(AUTH_LOG, { interval: 2000 }, () => {
    const newLines = fs.readFileSync(AUTH_LOG, "utf8").split("\n").slice(-20);
    newLines.forEach((line) => processLogLine(line));
  });
}

function processLogLine(line) {
  const now = Date.now();
  let match = line.match(RE_FAILED_SSH);
  if (!match) match = line.match(RE_FAILED_GENERIC);
  if (!match) return;

  const ip = match[1];
  if (cooldowns[ip] && now < cooldowns[ip]) return;

  if (!failedAttempts[ip]) failedAttempts[ip] = [];
  failedAttempts[ip].push(now);

  // Remove old entries
  failedAttempts[ip] = failedAttempts[ip].filter((t) => now - t < WINDOW_MS);

  if (failedAttempts[ip].length >= FAILED_THRESHOLD) {
    log(`🚨 Brute force detected from IP: ${ip}`);
    launchHoneypot("failed_login", ip);
    cooldowns[ip] = now + COOLDOWN_MS;
    failedAttempts[ip] = [];
  }
}

// ================= MAIN =================

log("🔰 Honeypot multi-trigger watcher started.");
watchFileDeletion();
watchFailedLogins();
*/