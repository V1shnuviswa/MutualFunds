# /home/ubuntu/order_management_system/src/utils.py
import re
from typing import Dict, Any

_camel_to_snake_pattern = re.compile(r"(.)([A-Z][a-z]+)")
_camel_to_snake_pattern2 = re.compile(r"([a-z0-9])([A-Z])")

def camel_to_snake(name: str) -> str:
    """Convert camelCase string to snake_case."""
    name = _camel_to_snake_pattern.sub(r"\1_\2", name)
    return _camel_to_snake_pattern2.sub(r"\1_\2", name).lower()

def convert_keys_to_snake_case(data: Any) -> Any:
    """Recursively convert dictionary keys from camelCase to snake_case."""
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = camel_to_snake(key)
            new_dict[new_key] = convert_keys_to_snake_case(value)
        return new_dict
    elif isinstance(data, list):
        return [convert_keys_to_snake_case(item) for item in data]
    else:
        return data

def preprocess_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess API request payload.
    
    This function:
    1. Converts camelCase keys to snake_case for compatibility with Pydantic models
    2. Handles any other data transformation needs
    
    Args:
        payload: The raw API request payload
        
    Returns:
        Processed payload with standardized key names and values
    """
    # Convert keys from camelCase to snake_case
    processed = convert_keys_to_snake_case(payload)
    
    # Additional preprocessing can be added here
    # For example, date format standardization, null handling, etc.
    
    return processed

