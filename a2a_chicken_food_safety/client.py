#!/usr/bin/env python3
"""
A2A Client for Chicken Food Safety Service
Implements the standard Agent-to-Agent HTTPS protocol with JSON messaging
"""

import json
import uuid
import requests
from datetime import datetime, timezone
import argparse
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChickenFoodSafetyClient:
    def __init__(self, server_url="http://localhost:8080"):
        """Initialize the A2A client"""
        self.server_url = server_url.rstrip('/')
        self.client_id = "chicken-food-safety-client"
        self.client_name = "Chicken Food Safety Client"
        self.version = "1.0"

    def create_a2a_request(self, food_item):
        """Create a standard A2A JSON request message"""
        return {
            "version": "1.0",
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "request",
            "sender": {
                "agent_id": self.client_id,
                "name": self.client_name,
                "version": self.version
            },
            "recipient": {
                "agent_id": "chicken-food-safety-service",
                "name": "Chicken Food Safety Service"
            },
            "payload": {
                "service": "chicken_food_safety_check",
                "food_item": food_item
            }
        }

    def check_food_safety(self, food_item):
        """Send A2A request to check food safety for chickens"""
        try:
            # Create A2A request message
            request_msg = self.create_a2a_request(food_item)

            logger.info(f"Sending A2A request for food item: {food_item}")

            # Send HTTPS request to server
            response = requests.post(
                f"{self.server_url}/a2a/chicken-food-safety",
                json=request_msg,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': f'{self.client_name}/{self.version}'
                },
                timeout=30
            )

            # Check HTTP status
            if response.status_code != 200:
                logger.error(f"HTTP error: {response.status_code}")
                return None, f"Server error: {response.status_code}"

            # Parse A2A response
            response_msg = response.json()

            # Validate A2A response format
            if not self.validate_a2a_response(response_msg, request_msg["id"]):
                return None, "Invalid A2A response format"

            # Check if request was successful
            if not response_msg["payload"]["success"]:
                error = response_msg["payload"].get("error", {})
                return None, f"Service error: {error.get('message', 'Unknown error')}"

            # Return the result
            result = response_msg["payload"]["result"]
            logger.info(f"Received response for {food_item}: {result['status']}")

            return result, None

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            return None, f"Network error: {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return None, f"Invalid JSON response: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None, f"Unexpected error: {str(e)}"

    def validate_a2a_response(self, response_msg, request_id):
        """Validate A2A response message format"""
        required_fields = ["version", "id", "timestamp", "type", "payload"]

        for field in required_fields:
            if field not in response_msg:
                logger.error(f"Missing required field in response: {field}")
                return False

        if response_msg["type"] != "response":
            logger.error("Response type must be 'response'")
            return False

        if response_msg.get("correlation_id") != request_id:
            logger.error("Correlation ID mismatch")
            return False

        if "success" not in response_msg["payload"]:
            logger.error("Missing 'success' in response payload")
            return False

        return True

    def discover_services(self):
        """Discover available services on the server"""
        try:
            response = requests.get(f"{self.server_url}/a2a/discovery", timeout=10)
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"Discovery failed: {response.status_code}"
        except Exception as e:
            return None, f"Discovery error: {str(e)}"

    def health_check(self):
        """Check server health"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=10)
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"Health check failed: {response.status_code}"
        except Exception as e:
            return None, f"Health check error: {str(e)}"

def format_result(result):
    """Format the safety check result for display"""
    if result["is_safe"] is True:
        status_color = "✅"
    elif result["is_safe"] is False:
        status_color = "❌"
    else:
        status_color = "❓"

    return f"""
{status_color} Food Safety Check Result:
Food Item: {result['food_item']}
Status: {result['status'].upper()}
Safe for Chickens: {result['is_safe']}
Message: {result['message']}
"""

def main():
    parser = argparse.ArgumentParser(description='A2A Client for Chicken Food Safety Service')
    parser.add_argument('--server', default='http://localhost:8080',
                       help='Server URL (default: http://localhost:8080)')
    parser.add_argument('--food', type=str,
                       help='Food item to check (interactive mode if not provided)')
    parser.add_argument('--discover', action='store_true',
                       help='Discover available services')
    parser.add_argument('--health', action='store_true',
                       help='Check server health')

    args = parser.parse_args()

    client = ChickenFoodSafetyClient(args.server)

    # Handle discovery request
    if args.discover:
        services, error = client.discover_services()
        if error:
            print(f"Error: {error}")
            sys.exit(1)
        print("Available Services:")
        print(json.dumps(services, indent=2))
        return

    # Handle health check
    if args.health:
        health, error = client.health_check()
        if error:
            print(f"Error: {error}")
            sys.exit(1)
        print("Server Health:")
        print(json.dumps(health, indent=2))
        return

    # Handle food safety check
    if args.food:
        # Single food item check
        result, error = client.check_food_safety(args.food)
        if error:
            print(f"Error: {error}")
            sys.exit(1)
        print(format_result(result))
    else:
        # Interactive mode
        print("🐔 Chicken Food Safety Checker (A2A Client)")
        print(f"Connected to: {args.server}")
        print("Type food items to check their safety for chickens.")
        print("Type 'quit' or 'exit' to stop.\n")

        while True:
            try:
                food_item = input("Enter food item: ").strip()

                if not food_item:
                    continue

                if food_item.lower() in ['quit', 'exit']:
                    print("Goodbye!")
                    break

                result, error = client.check_food_safety(food_item)

                if error:
                    print(f"❌ Error: {error}")
                else:
                    print(format_result(result))

                print()  # Empty line for readability

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()
