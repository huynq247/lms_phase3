"""
Response standardization middleware for consistent ID format
"""
from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import json
from typing import Any, Dict, List, Union

class ResponseStandardizer:
    """Middleware to standardize API responses"""
    
    @staticmethod
    def standardize_ids(data: Any) -> Any:
        """Convert MongoDB _id to standard id field"""
        if isinstance(data, dict):
            # Make a copy to avoid mutating original
            result = {}
            
            for key, value in data.items():
                if key == "_id":
                    # Convert _id to id
                    result["id"] = str(value)
                else:
                    # Recursively process nested objects
                    result[key] = ResponseStandardizer.standardize_ids(value)
                    
            return result
            
        elif isinstance(data, list):
            # Process list items
            return [ResponseStandardizer.standardize_ids(item) for item in data]
            
        else:
            # Return primitive values as-is
            return data
    
    @staticmethod
    def create_standardized_response(data: Any, status_code: int = 200) -> JSONResponse:
        """Create response with standardized ID format"""
        # Convert to JSON-serializable format first
        serializable_data = jsonable_encoder(data)
        # Then standardize IDs
        standardized_data = ResponseStandardizer.standardize_ids(serializable_data)
        return JSONResponse(content=standardized_data, status_code=status_code)
    
    @staticmethod
    def standardize_response_data(response_data: Dict) -> Dict:
        """Standardize response data for manual processing"""
        return ResponseStandardizer.standardize_ids(response_data)
