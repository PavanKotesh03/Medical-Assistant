"""
Simple test script to verify the API is working
Run this after starting the API server
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_root():
    """Test root endpoint"""
    print_section("Testing GET /")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API Status: {data.get('status', 'N/A')}")
            print(f"✓ Message: {data.get('message', 'N/A')}")
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_symptoms():
    """Test symptoms endpoint"""
    print_section("Testing GET /api/symptoms")
    
    try:
        response = requests.get(f"{BASE_URL}/api/symptoms")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Total Symptoms: {data.get('total_count', 0)}")
            if data.get('symptoms'):
                print(f"✓ Sample symptoms: {', '.join([s['name'] for s in data['symptoms'][:5]])}")
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_diseases():
    """Test diseases endpoint"""
    print_section("Testing GET /api/diseases")
    
    try:
        response = requests.get(f"{BASE_URL}/api/diseases")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Total Diseases: {data.get('total_count', 0)}")
            if data.get('diseases'):
                print(f"✓ Sample diseases: {', '.join([d['name'] for d in data['diseases'][:3]])}")
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_diagnose():
    """Test diagnosis endpoint"""
    print_section("Testing POST /api/diagnose")
    
    payload = {
        "symptom_names": ["fever", "headache", "cough"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/diagnose",
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")  # Print first 500 chars
        
        if response.status_code == 200:
            data = response.json()
            
            if 'status' not in data:
                print("✗ Response missing 'status' field")
                return False
            
            print(f"✓ Status: {data['status']}")
            print(f"✓ Message: {data['message']}")
            print(f"✓ Input Symptoms: {', '.join(data.get('input_symptoms', []))}")
            print(f"✓ Matched Symptoms: {', '.join(data.get('matched_symptoms', []))}")
            print(f"✓ Results Found: {len(data.get('results', []))}")
            
            if data.get('results'):
                print(f"\nTop 3 Results:")
                for i, result in enumerate(data['results'][:3], 1):
                    print(f"\n  {i}. {result['disease_name']}")
                    print(f"     Confidence: {result['confidence_score']}%")
                    print(f"     Match: {result['match_count']}/{result['total_symptoms']} symptoms")
                    if result.get('recommendations'):
                        print(f"     Recommendations: {', '.join(result['recommendations'][:2])}")
            
            return True
        else:
            print(f"✗ Failed with status {response.status_code}")
            return False
            
    except requests.exceptions.JSONDecodeError as e:
        print(f"✗ Invalid JSON response: {e}")
        print(f"Raw response: {response.text}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n🏥 Medical Symptom Assistant - API Test Suite")
    print("=" * 60)
    
    try:
        results = {
            "Root Endpoint": test_root(),
            "Symptoms Endpoint": test_symptoms(),
            "Diseases Endpoint": test_diseases(),
            "Diagnose Endpoint": test_diagnose()
        }
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        total = len(results)
        passed = sum(results.values())
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n✅ All tests completed successfully!")
        else:
            print("\n⚠️ Some tests failed. Check the output above.")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API at http://localhost:8000")
        print("\nMake sure the server is running:")
        print("  python -m app.main")
        print("\nOr if using uvicorn directly:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()