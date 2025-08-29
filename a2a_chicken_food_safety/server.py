#!/usr/bin/env python3
"""
A2A Server for Chicken Food Safety Service
Implements the standard Agent-to-Agent HTTPS protocol with JSON messaging
"""

import json
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Chicken food safety database
SAFE_FOODS = {
    'corn', 'wheat', 'oats', 'barley', 'rice', 'quinoa', 'millet',
    'lettuce', 'spinach', 'kale', 'cabbage', 'broccoli', 'carrots',
    'peas', 'green beans', 'squash', 'pumpkin', 'cucumber',
    'tomatoes', 'bell peppers', 'zucchini', 'sweet potato',
    'apples', 'berries', 'grapes', 'melon', 'banana',
    'chicken feed', 'layer feed', 'scratch grains',
    'sunflower seeds', 'pumpkin seeds', 'herbs', 'clover'
}

UNSAFE_FOODS = {
    'chocolate', 'avocado', 'onions', 'garlic', 'mushrooms',
    'raw beans', 'raw potatoes', 'green tomatoes', 'rhubarb',
    'apple seeds', 'cherry pits', 'caffeine', 'alcohol',
    'moldy food', 'salty snacks', 'candy', 'processed food'
}

def create_a2a_response(request_msg, success=True, result=None, error=None):
    """Create a standard A2A JSON response message"""
    response = {
        "version": "1.0",
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "response",
        "correlation_id": request_msg.get("id"),
        "sender": {
            "agent_id": "chicken-food-safety-service",
            "name": "Chicken Food Safety Service",
            "version": "1.0"
        },
        "recipient": request_msg.get("sender", {}),
        "payload": {
            "success": success,
            "service": "chicken_food_safety_check"
        }
    }

    if success and result is not None:
        response["payload"]["result"] = result
    elif not success and error:
        response["payload"]["error"] = error

    return response

def validate_a2a_request(msg):
    """Validate A2A request message format"""
    required_fields = ["version", "id", "timestamp", "type", "sender", "payload"]

    for field in required_fields:
        if field not in msg:
            return False, f"Missing required field: {field}"

    if msg["type"] != "request":
        return False, "Message type must be 'request'"

    if "service" not in msg["payload"]:
        return False, "Missing 'service' in payload"

    if msg["payload"]["service"] != "chicken_food_safety_check":
        return False, "Unknown service requested"

    if "food_item" not in msg["payload"]:
        return False, "Missing 'food_item' in payload"

    return True, None

def check_food_safety(food_item):
    """Check if a food item is safe for chickens"""
    food_lower = food_item.lower().strip()

    if food_lower in SAFE_FOODS:
        return {
            "food_item": food_item,
            "is_safe": True,
            "status": "safe",
            "message": f"{food_item} is safe for chickens to eat."
        }
    elif food_lower in UNSAFE_FOODS:
        return {
            "food_item": food_item,
            "is_safe": False,
            "status": "unsafe",
            "message": f"{food_item} is NOT safe for chickens and should be avoided."
        }
    else:
        return {
            "food_item": food_item,
            "is_safe": None,
            "status": "unknown",
            "message": f"Safety information for {food_item} is not available. Please consult a veterinarian."
        }

@app.route('/a2a/chicken-food-safety', methods=['POST'])
def chicken_food_safety():
    """A2A endpoint for chicken food safety checks"""
    try:
        # Parse JSON request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        request_msg = request.get_json()
        logger.info(f"Received A2A request: {request_msg.get('id')}")

        # Validate A2A message format
        is_valid, error_msg = validate_a2a_request(request_msg)
        if not is_valid:
            logger.warning(f"Invalid A2A request: {error_msg}")
            response = create_a2a_response(
                request_msg,
                success=False,
                error={"code": "INVALID_REQUEST", "message": error_msg}
            )
            return jsonify(response), 400

        # Extract food item from payload
        food_item = request_msg["payload"]["food_item"]

        # Check food safety
        result = check_food_safety(food_item)

        # Create A2A response
        response = create_a2a_response(request_msg, success=True, result=result)

        logger.info(f"Processed food safety check for '{food_item}': {result['status']}")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        response = create_a2a_response(
            request_msg if 'request_msg' in locals() else {},
            success=False,
            error={"code": "INTERNAL_ERROR", "message": "Internal server error"}
        )
        return jsonify(response), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "chicken-food-safety-service",
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/a2a/discovery', methods=['GET'])
def service_discovery():
    """A2A service discovery endpoint"""
    return jsonify({
        "services": [
            {
                "name": "chicken_food_safety_check",
                "description": "Check if a food item is safe for chickens",
                "endpoint": "/a2a/chicken-food-safety",
                "method": "POST",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "food_item": {
                            "type": "string",
                            "description": "Name of the food item to check"
                        }
                    },
                    "required": ["food_item"]
                }
            }
        ]
    })

def main():
    print("Starting Chicken Food Safety A2A Server...")
    print("Endpoints:")
    print("  POST /a2a/chicken-food-safety - Main A2A service endpoint")
    print("  GET  /health - Health check")
    print("  GET  /a2a/discovery - Service discovery")

    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == '__main__':
    main()
