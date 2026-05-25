from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import urllib.parse
import logging
import sys
import re

app = Flask(__name__)
# Enable CORS for communication with your frontend dashboard
CORS(app, resources={r"/api/*": {"origins": "*"}})

# GLOBAL SYSTEM STATE
automation_lock = threading.Lock()
active_driver = None

# CENTRAL REGISTRY MECHANISM
PLATFORM_REGISTRY = {
    "amazon": {
        "base_url": "https://www.amazon.in",
        "search_path": "/s?k=",
        "has_automation": True
    },
    "flipkart": {
        "base_url": "https://www.flipkart.com",
        "search_path": "/search?q=",
        "has_automation": False
    },
    "myntra": {
        "base_url": "https://www.myntra.com",
        "search_path": "/",
        "aliases": ["fashion", "clothes", "shopping"],
        "has_automation": False
    },
    "google maps": {
        "base_url": "https://www.google.com/maps",
        "search_path": "/search/",
        "aliases": ["map", "route", "direction", "location"],
        "has_automation": False
    },
    "gmail": {
        "base_url": "https://mail.google.com",
        "search_path": "/mail/u/0/#search/",
        "aliases": ["mail", "inbox"],
        "has_automation": False
    },
    "youtube": {
        "base_url": "https://www.youtube.com",
        "search_path": "/results?search_query=",
        "aliases": ["video", "song", "music"],
        "has_automation": False
    },
    "news": {
        "base_url": "https://news.google.com",
        "search_path": "/search?q=",
        "aliases": ["world news", "global news", "updates", "breaking news", "current affairs"],
        "has_automation": False
    },
    "github": {
        "base_url": "https://github.com",
        "search_path": "/search?q=",
        "has_automation": False
    },
    "linkedin": {
        "base_url": "https://www.linkedin.com",
        "search_path": "/search/results/all/?keywords=",
        "has_automation": False
    }
}

def resolve_intent_and_query(command):
    command = command.lower().strip()
    matched_platform = None

    # Sort platforms by text boundary length to protect multi-phrase definitions
    sorted_platforms = sorted(
        PLATFORM_REGISTRY.items(), 
        key=lambda item: max([len(term) for term in [item[0]] + item[1].get("aliases", [])]), 
        reverse=True
    )

    for target_key, config in sorted_platforms:
        search_terms = [target_key] + config.get("aliases", [])
        for term in search_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', command):
                matched_platform = target_key
                command = re.sub(r'\b' + re.escape(term) + r'\b', '', command).strip()
                break
        if matched_platform:
            break

    # Clean filler patterns and relational prepositions
    action_patterns = [
        r"\btell me about\b", r"\bdetails of\b", r"\bsearch for\b", 
        r"\bopen up\b", r"\broute to\b", r"\bshow me\b", r"\bgo to\b", 
        r"\bsearch\b", r"\blaunch\b", r"\bstart\b", r"\bplay\b", r"\bfind\b", r"\bopen\b",
        r"\bon\b", r"\bfor\b", r"\bat\b", r"\band\b"
    ]
    
    clean_query = command
    for pattern in action_patterns:
        clean_query = re.sub(pattern, " ", clean_query)
    
    extracted_query = " ".join(clean_query.split())
    return matched_platform, extracted_query

def build_api_payload(status, action, url=""):
    return jsonify({"status": status, "action": action, "url": url})

def execute_amazon_pipeline():
    global active_driver
    if not automation_lock.acquire(blocking=False):
        print("[WORKER BLOCKED] Execution framework locked.")
        return
        
    print("\n[SELENIUM] Initializing autonomous pipeline infrastructure...")
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("detach", True)
        
        active_driver = webdriver.Chrome(options=options)
        active_driver.get(PLATFORM_REGISTRY["amazon"]["base_url"])
        
        wait = WebDriverWait(active_driver, 12)
        signin_node = wait.until(EC.element_to_be_clickable((By.ID, "nav-link-accountList")))
        signin_node.click()
        print("[SELENIUM] Verification Complete: Target node accessed successfully.")
    except Exception as error:
        print(f"[SELENIUM ERROR] Automation engine failure: {error}", file=sys.stderr)
        if active_driver:
            try: active_driver.quit()
            except: pass
            active_driver = None
    finally:
        automation_lock.release()

@app.route("/api/command", methods=["POST"])
def process_incoming_command():
    try:
        payload = request.get_json(force=True) or {}
        raw_input = payload.get("command", "").strip()
        
        if not raw_input:
            return build_api_payload("empty", "No command structural data identified.")
            
        command = raw_input.lower()
        print(f"[INGRESS] Operational Vector -> {command}")
        
        if any(token in command for token in ["system", "status", "connected", "dashboard"]):
            return build_api_payload("success", "Dynamic infrastructure routing node online.")
            
        platform, query = resolve_intent_and_query(command)
        
        if platform:
            platform_config = PLATFORM_REGISTRY[platform]
            
            # Catch runner conditions for automated system scripts
            if platform_config["has_automation"] and any(act in command for act in ["login", "automation", "run"]):
                if automation_lock.locked():
                    return build_api_payload("busy", "Automation pipeline is running another process.")
                
                threading.Thread(target=execute_amazon_pipeline, daemon=True).start()
                return build_api_payload("success", f"Launching underlying browser runner for {platform}.", platform_config["base_url"])
            
            if query:
                if platform == "myntra":
                    target_url = f"{platform_config['base_url']}/{urllib.parse.quote(query)}"
                else:
                    target_url = f"{platform_config['base_url']}{platform_config['search_path']}{urllib.parse.quote(query)}"
                return build_api_payload("success", f"Routing to {platform} query parameter: '{query}'", target_url)
            
            return build_api_payload("success", f"Direct interface redirection for {platform}.", platform_config["base_url"])
            
        fallback_target = f"https://www.google.com/search?q={urllib.parse.quote(command)}"
        return build_api_payload("success", f"Forwarding query parameters to open web search fallback.", fallback_target)
            
    except Exception as runtime_error:
        print(f"[CRITICAL] Runtime pipeline error: {runtime_error}", file=sys.stderr)
        return jsonify({"status": "error", "action": "Internal parsing pipeline failure.", "details": str(runtime_error)}), 500

@app.route("/api/close_session", methods=["POST"])
def terminate_orphaned_drivers():
    global active_driver
    try:
        if active_driver:
            active_driver.quit()
            active_driver = None
            return build_api_payload("success", "Detached browser resources recovered successfully.")
        return build_api_payload("empty", "No orphaned browser processes found running.")
    except Exception as error:
        return build_api_payload("error", f"Node process recovery exception: {str(error)}")

@app.route("/")
def health_check():
    return jsonify({"status": "online", "engine": "Dynamic Registry Router"})

if __name__ == "__main__":
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    print("\n" + "=" * 65 + "\n    BACKEND OPERATIONAL SYSTEM LOGGED ON\n" + "=" * 65 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
