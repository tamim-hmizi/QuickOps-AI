import pytest
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8001"

# Test cases: file path and expected recommendation
TEST_CASES = [
    ("tests/vm_test.json", "VM"),
    ("tests/k8s_test.json", "KUBERNETES"),
]

@pytest.mark.parametrize("json_path,expected_recommendation", TEST_CASES)
def test_analyze_deployment(json_path, expected_recommendation):
    json_file = Path(json_path)
    assert json_file.exists(), f"Test file {json_path} does not exist."

    with open(json_file, "r") as f:
        payload = json.load(f)

    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    
    assert response.status_code == 200, f"API returned status {response.status_code}"

    data = response.json()
    
    assert "recommendation" in data, "Response missing 'recommendation' field."
    
    recommendation = data["recommendation"].upper()
    
    assert recommendation == expected_recommendation, (
        f"Expected recommendation '{expected_recommendation}' but got '{recommendation}'.\n"
        f"Full response: {json.dumps(data, indent=2)}"
    )
