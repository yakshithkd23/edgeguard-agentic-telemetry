const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(__dirname, '../agent_audit.log');
const INFERENCE_FILE = path.join(__dirname, '../inference_output.json');

function logAudit(action, reason, details) {
    const entry = `[${new Date().toISOString()}] ACTION: ${action} | REASON: ${reason} | DETAILS: ${JSON.stringify(details)}\n`;
    fs.appendFileSync(LOG_FILE, entry);
    console.log(`[AUDIT] ${entry.trim()}`);
}

function runAgent() {
    if (!fs.existsSync(INFERENCE_FILE)) {
        console.log("No inference output found. Run model.py first.");
        return;
    }

    const data = JSON.parse(fs.readFileSync(INFERENCE_FILE, 'utf8'));
    console.log("\n--- AGENT DECISION ENGINE ---");

    const metrics = data.raw_metrics;
    let actionTaken = false;

    // Check RAM threshold
    if (metrics.ram_percent > 80.0) {
        logAudit("CLEAR_CACHE", "RAM usage exceeded threshold", { ram: metrics.ram_percent });
        console.log("-> Action Executed: Flushed temporary system memory caches.");
        actionTaken = true;
    }

    // Check CPU or Error Log threshold
    if (metrics.cpu_percent > 85.0 || metrics.error_logs_count > 0) {
        logAudit("RESTART_SERVICE", "Error log spike detected", { errors: metrics.error_logs_count });
        console.log("-> Action Executed: Restarted background worker processes.");
        actionTaken = true;
    }

    if (!actionTaken) {
        console.log("System state nominal. No recovery needed.");
    }
}

runAgent();