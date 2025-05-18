#--🚀 Imports
from flask import Flask, render_template, request, redirect, url_for
from app.missions.recon import run_recon
from app.missions.engineering import run_engineering
from app.missions.encryption import run_encryption
from app.analytics.market_feed import get_market_summary
from app.analytics.screener import get_top_movers
from app.analytics.chart_fetcher import get_chart_html
from app.analytics.data_collector import log_commander_victory
from app.system.mission_logger import log_mission
from app.system.log_viewer import get_recent_logs
from app.system.settings_manager import load_settings, update_setting
from app.system.mission_registry import get_all_commands
from app.system.intel_registry import log_intel, get_recent_intel
from app.system.session_time_engine import get_current_session, start_session_engine
from app.system.insight_engine import generate_commander_insight
from app.core.chiefs.chief_router import route_chief_action, route_to_chief
from utils.logging.chief_log_writer import log_chief_response
from app.chiefs import gota, rapid, engineering, blackops, intel
from fastapi import Request, Form, FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
import yaml
import os
from datetime import datetime

#--⚙️ App Initialization
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
commander_authenticated = False

#--📋 Mission States
mission_archive = []
active_missions = []

#--🛠️ Commander Missions
mission_modules = {
    'start recon': run_recon,
    'start engineering': run_engineering,
    'start encryption': run_encryption,
    'start chart': lambda: get_chart_html('AAPL', '1DAY', 'mock'),
}

#--📊 Basic Commands
basic_commands = {
    'status': "All systems are operational, Commander.",
    'chiefs': "Chiefs of Staff standing by...",
    'mission': "DoyenView MVPv0.01 initialized. Awaiting instructions.",
    'show missions': "Displaying mission archive, Commander.",
    'status missions': "Displaying active mission status.",
    'start market feed': get_market_summary,
    'start screener': get_top_movers,
    'view logs': get_recent_logs,
}

#--🔐 Auth
def authenticate_commander(input_password):
    try:
        with open('app/system/auth_config.txt', 'r') as file:
            return input_password == file.read().strip()
    except FileNotFoundError:
        return False

#--📊 Tooltip log enrichment
def enrich_chiefs_with_logs(config):
    for chief in config['chiefs']:
        log_path = f"models/Chiefs/Logs/{chief['id']}.yaml"
        chief['memory_snapshots'] = []

        try:
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    logs = yaml.safe_load(f) or []
                    if logs:
                        last_logs = logs[-3:]
                        chief['memory_snapshots'] = last_logs
                        last = logs[-1]
                        chief['last_command'] = last.get('command', 'None')
                        chief['last_response'] = last.get('response', 'None')
                        chief['last_timestamp'] = last.get('timestamp', 'None')
                    else:
                        chief['last_command'] = "None"
                        chief['last_response'] = "None"
                        chief['last_timestamp'] = "None"
            else:
                chief['last_command'] = "None"
                chief['last_response'] = "None"
                chief['last_timestamp'] = "None"
        except Exception:
            chief['last_command'] = chief['last_response'] = chief['last_timestamp'] = 'Unavailable'

#--🕒 API Session
@app.route('/current_session', methods=['GET'])
def current_session():
    return {'session': get_current_session()}

#--🔐 Login
@app.route('/', methods=['GET', 'POST'])
def home():
    global commander_authenticated
    settings = load_settings()
    if not commander_authenticated:
        if request.method == 'POST':
            if authenticate_commander(request.form.get('password')):
                commander_authenticated = True
                return render_template('index.html', settings=settings)
            return render_template('login.html', error="Access Denied.")
        return render_template('login.html')
    return render_template('index.html', settings=settings)

#--🧠 Execute Main Command
@app.route('/execute', methods=['POST'])
def execute():
    if not commander_authenticated:
        return redirect(url_for('home'))

    command = request.form.get('command')
    if command == "launch insight": command = "view intel"

    response = handle_command(command)
    settings = load_settings()

    if command == "view intel":
        return render_template('index.html', intel_logs=get_recent_intel(), insights=generate_commander_insight(), settings=settings)
    if command == "view logs":
        return render_template('index.html', mission_logs=get_recent_logs(), settings=settings)
    if isinstance(response, list) and all(isinstance(x, str) for x in response):
        return render_template('index.html', mission_logs=response, settings=settings)
    if isinstance(response, str) and response.startswith("https://"):
        return render_template('index.html', chart_url=response, settings=settings)
    if isinstance(response, dict):
        if "Top Gainers" in response:
            return render_template('index.html', screener=response, settings=settings)
        return render_template('index.html', market_feed=response, settings=settings)
    return render_template('index.html', response=response, settings=settings)

#--💬 Command Logic
def handle_command(command):
    command = command.lower()
    if command.startswith("set "):
        try:
            _, key, value = command.split(' ', 2)
            update_setting(key, value)
            return f"Commander Setting Updated: {key} = {value}"
        except Exception as e:
            return f"Failed to update setting: {str(e)}"
    if command == "run diagnostics":
        return [f"[✅] {cmd}" if not isinstance(handle_command(cmd), Exception) else f"[❌] {cmd}" for cmd in mission_modules | basic_commands]

    command_map = get_all_commands()
    if command in command_map:
        result = command_map[command]
        if callable(result): result = result()
        log_mission(command, result, status="Success")
        if command in mission_modules:
            if command not in active_missions:
                active_missions.append(command)
            mission_archive.append(command)
        return result

    return "Unknown command. Please refine your input."

#--🧠 Chiefs UI
@app.route('/chiefs')
def chiefs_panel():
    settings = load_settings()
    with open('models/Chiefs/Configs/chiefs_manifest.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    enrich_chiefs_with_logs(config)
    return render_template('chiefs.html', chiefs=config['chiefs'], settings=settings)

@app.route('/chief/<chief_name>', endpoint='load_chief')
def load_chief(chief_name):
    settings = load_settings()
    with open('models/Chiefs/Configs/chiefs_manifest.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    enrich_chiefs_with_logs(config)
    selected = next((c for c in config['chiefs'] if c['id'] == chief_name), None)
    return render_template('chiefs.html',
        chiefs=config['chiefs'],
        selected_chief=selected,
        settings=settings,
        session_context=get_current_session(),
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route("/chief/route", methods=["POST"])
def route_generic_chief_command():
    command = request.form.get("command", "")
    reply = route_to_chief(command)
    return redirect(url_for('chiefs_panel', reply=reply))

@app.route('/chiefs/<chief_id>/command', methods=['POST'])
def subcommand_unified(chief_id):
    goal = request.form.get('goal')
    settings = load_settings()
    output = route_chief_action(chief_id, goal)

    with open('models/Chiefs/Configs/chiefs_manifest.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    enrich_chiefs_with_logs(config)
    selected = next((c for c in config['chiefs'] if c['id'] == chief_id), None)

    try:
        with open(f'models/Chiefs/Logs/{chief_id}.yaml', 'r', encoding='utf-8') as f:
            chief_logs = yaml.safe_load(f) or []
    except Exception:
        chief_logs = []

    return render_template('chiefs.html',
        chiefs=config['chiefs'],
        selected_chief=selected,
        chief_output=output,
        settings=settings,
        session_context=get_current_session(),
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        **{f"{chief_id}_logs": chief_logs}
    )

#--📡 Agent2Agent
@app.route("/agent/route", methods=["POST"])
def agent_to_agent_route():
    from_chief = request.form.get("from")
    to_chief = request.form.get("to")
    message = request.form.get("message")
    reply = route_to_chief(f"{to_chief}: {message}")
    return {"status": "ok", "reply": reply}

@app.route('/intel')
def intel():
    logs = get_recent_intel()
    settings = load_settings()
    return render_template('index.html', intel_logs=logs, show_debrief=True, settings=settings)

#--📈 Chart Routes
@app.route("/chart")
def chart_redirect():
    return redirect(url_for("render_chart", symbol="AAPL", interval="1DAY", mode="mock"))

import os

def list_mock_symbols():
    symbols = set()
    if os.path.exists("mock_engine_cache"):
        for file in os.listdir("mock_engine_cache"):
            if file.endswith(".csv") and "_" in file:
                sym = file.split("_")[0]
                symbols.add(sym.upper())
    return sorted(list(symbols))

@app.route("/chart/<symbol>")
def render_chart(symbol):
    interval = request.args.get("interval", "1DAY")
    mode = request.args.get("mode", "mock")
    volume_toggle = request.args.get("volume", "on")
    chart_type = request.args.get("chart_type", "candlestick")
    intel_on = request.args.get("intel", "off") == "on"
    pulse_on = request.args.get("pulse", "off") == "on"
    study_rsi_on = request.args.get("study_rsi", "off") == "on"


    show_volume = volume_toggle == "on"

    chart_html = get_chart_html(
        symbol, interval, mode,
        show_volume=show_volume,
        chart_type=chart_type,
        intel_layer=intel_on,
        pulse_dot=pulse_on,
        study_rsi=study_rsi_on
    )


    settings = load_settings()
    return render_template(
        "chart_viewer.html",
        chart_html=chart_html,
        selected_symbol=symbol.upper(),
        selected_interval=interval,
        selected_mode=mode,
        selected_volume=volume_toggle,
        selected_chart_type=chart_type,
        selected_intel='on' if intel_on else 'off',
        selected_pulse='on' if pulse_on else 'off',
        selected_study_rsi='on' if study_rsi_on else 'off',
        available_symbols=list_mock_symbols(),
        settings=settings
    )


@app.route('/intro')
def intro():
    return render_template("intro.html")


from flask import jsonify

@app.route("/chat", methods=["POST"])
def chat_input():
    data = request.get_json()
    message = data.get("message", "").strip().lower()

    # 🧠 AI-style Command Routing
    if message.startswith("run rsi"):
        return jsonify({"reply": "🔍 Running RSI strategy on current chart..."})
    elif "vix" in message:
        return jsonify({"reply": "🧠 VIX is currently elevated. Risk is high."})
    elif "start screener" in message:
        return jsonify({"reply": "🛰 Launching screener module..."})
    elif "hello" in message:
        return jsonify({"reply": "👋 Hello, Commander. How can I assist you today?"})
    else:
        # Placeholder: No route yet
        return jsonify({"reply": f"🤖 You said: “{message}” — command not recognized (yet)."})




#--🚀 Boot
if __name__ == "__main__":
    start_session_engine()
    app.run(debug=True)

#--📡 FastAPI Backup
fastapi_app = FastAPI()

@fastapi_app.post("/api/execute")
async def execute_command(request: Request):
    data = await request.json()
    command = data.get("command")
    if not command:
        return JSONResponse(content={"reply": "No command provided."}, status_code=400)
    reply = route_to_chief(command)
    return JSONResponse(content={"reply": reply})
