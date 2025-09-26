from flask import Blueprint, request, jsonify
from services.automation_service import AutomationService
from utils.intent_detection import detect_form_type
import logging
import asyncio
from services.fallback_form_filler import run_fallback_form_filler

logger = logging.getLogger(__name__)

browser_bp = Blueprint('browser', __name__, url_prefix='/api/browser')
automation_service = AutomationService()

@browser_bp.route('/execute', methods=['POST'])
async def handle_browser_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "form_data is required"}), 400
    user_prompt = data.get('user_prompt', '')
    form_type = detect_form_type(user_prompt)
    current_status = data.get('current_status') or {
        "step_index": 0,
        "current_step_summary": "",
        "url": "",
        "awaiting_user_input": False,
        "requested_input_type": None,
        "task_complete": False,
        "error_message": "",
        "next_expected_action": "",
        "page_state": ""
    }
    form_data = data.get('form_data', {})
    if form_type == "fallback":
        # Run the fallback form filler for unknown prompts
        await run_fallback_form_filler(user_prompt, form_data)
        return jsonify({"status": "fallback_executed"})
    response_data = await automation_service.run_automation(current_status, form_data, form_type)
    return jsonify(response_data)

@browser_bp.route('/submit_input', methods=['POST'])
async def submit_user_input():
    data = request.get_json()
    if not data:
        return jsonify({"error": "input_data is required"}), 400
    input_type = data.get('input_type')
    input_value = data.get('input_value')
    if not input_type or not input_value:
        return jsonify({"error": "input_type and input_value are required"}), 400
    result = await automation_service.submit_user_input(input_type, input_value)
    return jsonify(result)

@browser_bp.route('/status', methods=['GET'])
async def get_browser_status():
    state = await automation_service.get_browser_status()
    return jsonify(state)

@browser_bp.route('/reset', methods=['POST'])
async def reset_browser():
    result = await automation_service.reset_browser()
    return jsonify(result) 