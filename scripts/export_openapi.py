"""
Script to export OpenAPI specification for frontend teams
"""
import json
import requests
from datetime import datetime

def export_openapi_spec():
    """Export OpenAPI specification from running server"""
    
    try:
        # Get OpenAPI spec from running server
        response = requests.get("http://localhost:8000/openapi.json")
        response.raise_for_status()
        
        openapi_spec = response.json()
        
        # Add frontend-specific metadata
        openapi_spec["info"]["title"] = "Flashcard LMS Backend API"
        openapi_spec["info"]["description"] = """
## Flashcard LMS Backend API Documentation

Complete API documentation for frontend integration.

### Authentication
All protected endpoints require Bearer token authentication:
```
Authorization: Bearer <access_token>
```

### Test Accounts
- **Admin**: admin@flashcard.com / admin123
- **Teacher**: teacher@flashcard.com / teacher123  
- **Student**: test@example.com / test123

### Base URL
Development: `http://localhost:8000`

### Repository
https://github.com/huynq247/lms_phase3
"""
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"openapi_spec_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
        
        print(f"✅ OpenAPI specification exported to: {filename}")
        
        # Also save as latest
        with open("openapi_spec_latest.json", 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Latest specification saved as: openapi_spec_latest.json")
        
        # Print summary
        endpoints = []
        for path, methods in openapi_spec.get("paths", {}).items():
            for method in methods.keys():
                endpoints.append(f"{method.upper()} {path}")
        
        print(f"\n📊 API Summary:")
        print(f"   - Total endpoints: {len(endpoints)}")
        print(f"   - Authentication endpoints: {len([e for e in endpoints if '/auth/' in e])}")
        print(f"   - Health endpoints: {len([e for e in endpoints if '/health' in e])}")
        
        print(f"\n🔗 Available endpoints:")
        for endpoint in sorted(endpoints):
            print(f"   - {endpoint}")
            
        return filename
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend server")
        print("   Make sure the server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error exporting OpenAPI spec: {e}")
        return None

if __name__ == "__main__":
    export_openapi_spec()
