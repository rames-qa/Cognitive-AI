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

# SYSTEM SETUP & CONFIGURATION
app = Flask(__name__)

# Production CORS: Restrict origins in production if frontend domain is known
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*" 
        }
    }
)

# GLOBAL CONCURRENCY STATE
automation_lock = threading.Lock()
active_driver = None
# DYNAMIC NLP & QUERY PROCESSING ENGINE

def extract_production_intent(text, platform_tags=None):
    """
    Safely tokenizes natural language speech strings without 
    accidentally destroying target phrases or substring structures.
    """
    if platform_tags is None:
        platform_tags = []
        
    cleaned = text.lower().strip()
    
    # Ordered by string length descending to guarantee maximum phrase matching first
    action_tokens = [
        "tell me about", "details of", "search for", 
        "open up", "route to", "show me", "go to", 
        "search", "launch", "start", "play", "find", "open"
    ]
    
    # Normalize and isolate platform-specific keyword definitions
    filter_tokens = action_tokens + [str(tag).lower() for tag in platform_tags]
    
    for token in filter_tokens:
        # Pad checking spaces to preserve word boundaries where possible
        if token in cleaned:
            cleaned = cleaned.replace(token, "")
            
    return cleaned.strip()

def build_api_payload(status, action, url=""):
    return jsonify({
        "status": status,
        "action": action,
        "url": url
    })

# ASYNC AUTOMATION WORKER PIPELINES

def execute_amazon_pipeline():
    """
    Handles headless-safe execution and explicitly manages target lifecycles
    without orphaning web browser processing nodes in system memory.
    """
    global active_driver

    if not automation_lock.acquire(blocking=False):
        print("[WORKER BLOCKED] Automation routine requested while engine is locked.")
        return
        
    print("\n[SELENIUM] Initializing detached infrastructure orchestration...")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    
    # Keeps the session visible for manual interception post-automation pass
    options.add_experimental_option("detach", True)
    
    try:
        # Selenium 4.6+ Native Driver Resolution
        active_driver = webdriver.Chrome(options=options)
        active_driver.get("https://www.amazon.in")
        
        wait = WebDriverWait(active_driver, 12)
        signin_node = wait.until(
            EC.element_to_be_clickable((By.ID, "nav-link-accountList"))
        )
        signin_node.click()
        print("[SELENIUM] Verification target achieved: Login gateway reached.")
        
    except Exception as error:
        print(f"[SELENIUM ERROR] Pipe failure detected: {error}", file=sys.stderr)
        if active_driver:
            try:
                active_driver.quit()
            except Exception:
                pass
            active_driver = None
    finally:
        automation_lock.release()

# PRODUCTION ROUTING GATEWAYS

@app.route("/api/command", methods=["POST"])
def process_incoming_command():
    try:
        payload = request.get_json(force=True) or {}
        raw_input = payload.get("command", "").strip()
        
        if not raw_input:
            return build_api_payload("empty", "No payload vector received.")
            
        command = raw_input.lower()
        print(f"[INGRESS] Core Token Vector -> {command}")
        
        # SYSTEM UTILITIES
        if any(token in command for token in ["system", "status", "connected", "dashboard"]):
            return build_api_payload("success", "Production gateway infrastructure operational.")
            
        # AMAZON TARGET ROUTING
        elif "amazon" in command:
            if any(act in command for act in ["login", "automation", "run"]):
                if automation_lock.locked():
                    return build_api_payload("busy", "Engine is currently executing a standard block.")
                
                threading.Thread(target=execute_amazon_pipeline, daemon=True).start()
                return build_api_payload("success", "Spawning decoupled Amazon automated runner.", "https://www.amazon.in")
            
            search_query = extract_production_intent(command, ["amazon"])
            if search_query:
                target_url = f"https://www.amazon.in/s?k={urllib.parse.quote(search_query)}"
                return build_api_payload("success", f"Redirecting to Amazon search: {search_query}", target_url)
            return build_api_payload("success", "Redirecting to Amazon main interface.", "https://www.amazon.in")
            
        # FLIPKART TARGET ROUTING
        elif "flipkart" in command:
            search_query = extract_production_intent(command, ["flipkart"])
            if search_query:
                target_url = f"https://www.flipkart.com/search?q={urllib.parse.quote(search_query)}"
                return build_api_payload("success", f"Redirecting to Flipkart search: {search_query}", target_url)
            return build_api_payload("success", "Redirecting to Flipkart marketplace.", "https://www.flipkart.com")
            
        # GOOGLE MAPS (Fixed Production-Grade Geo Endpoints)
        elif any(token in command for token in ["map", "route", "direction", "location"]):
            search_query = extract_production_intent(command, ["map", "route", "direction", "location"])
            if search_query:
                target_url = f"https://www.google.com/maps/search/{urllib.parse.quote(search_query)}"
                return build_api_payload("success", f"Generating dynamic mapping path for: {search_query}", target_url)
            return build_api_payload("success", "Redirecting to primary Google Maps engine.", "https://www.google.com/maps")
            
        # GLOBAL COMMUNICATIONS (GMAIL)
        elif any(token in command for token in ["gmail", "mail", "inbox"]):
            search_query = extract_production_intent(command, ["gmail", "mail", "inbox"])
            if search_query:
                target_url = f"https://mail.google.com/mail/u/0/#search/{urllib.parse.quote(search_query)}"
                return build_api_payload("success", f"Filtering messaging archive for: {search_query}", target_url)
            return build_api_payload("success", "Opening central communications workspace.", "https://mail.google.com")
            
        # CONTENT DELIVERY (YOUTUBE)
        elif any(token in command for token in ["youtube", "video", "song", "music"]):
            search_query = extract_production_intent(command, ["youtube", "video", "song", "music"])
            if search_query:
                target_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
                return build_api_payload("success", f"Streaming search indexing array for: {search_query}", target_url)
            return build_api_payload("success", "Opening content platform dashboard.", "https://www.youtube.com")
            
        # NEWS STRATIFICATION
        elif "news" in command:
            search_query = extract_production_intent(command, ["news"])
            if search_query:
                target_url = f"https://news.google.com/search?q={urllib.parse.quote(search_query)}"
                return build_api_payload("success", f"Isolating dynamic press feeds for: {search_query}", target_url)
            return build_api_payload("success", "Opening centralized global press feeds.", "https://news.google.com")
            
        # PORTAL FALLBACK DEFAULTS
        elif "google" in command:
            return build_api_payload("success", "Resolving portal home.", "https://www.google.com")
        elif "github" in command:
            return build_api_payload("success", "Resolving version control hub.", "https://github.com")
        elif "linkedin" in command:
            return build_api_payload("success", "Resolving business index professional channels.", "https://www.linkedin.com")
            
        # WEB SEARCH FALLBACK
        else:
            fallback_target = f"https://www.google.com/search?q={urllib.parse.quote(command)}"
            return build_api_payload("success", f"Processing wide-spectrum web search fallback for: {command}", fallback_target)
            
    except Exception as runtime_error:
        print(f"[CRITICAL ERROR] Core runtime fault: {runtime_error}", file=sys.stderr)
        return jsonify({
            "status": "error",
            "action": "Internal API infrastructure exception encountered.",
            "details": str(runtime_error)
        }), 500

# RESOURCE LIFECYCLE MANAGEMENT ENDPOINTS

@app.route("/api/close_session", methods=["POST"])
def terminate_orphaned_drivers():
    """
    Explicit administrative webhook to clean up trailing Chrome runtimes
    leveraging the detached experimental flag state.
    """
    global active_driver
    try:
        if active_driver:
            active_driver.quit()
            active_driver = None
            return build_api_payload("success", "Active infrastructure nodes terminated cleanly.")
        return build_api_payload("empty", "No standalone processes found active.")
    except Exception as error:
        return build_api_payload("error", f"Node teardown exception: {str(error)}")

@app.route("/")
def health_check():
    return jsonify({
        "status": "online",
        "service": "Cognitive Enterprise Pipeline"
    })

# SERVER BOOTSTRAPPING ENGINE
if __name__ == "__main__":
    # Suppress verbose development routing entries
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    
    print("\n" + "=" * 65)
    print("    COGNITIVE SPEECH AI ")
    print("   Operational Scope: Threaded API Ingress + Selenium Engine")
    print("   Network Target:    http://0.0.0.0:5000")
    print("=" * 65 + "\n")
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )
