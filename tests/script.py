import requests
import json

def send_request(file_path, label):
    with open(file_path, "r") as f:
        data = json.load(f)

    print(f"\n🧪 Test: {label}")
    try:
        response = requests.post("http://localhost:8001/analyze", json=data)
        print("✅ Status Code:", response.status_code)
        print("📤 Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print("❌ Request failed:", str(e))

if __name__ == "__main__":
    send_request("tests/vm_test.json", "Should recommend VM")
    print("*******************")
    send_request("tests/k8s_test.json", "Should recommend Kubernetes")
    print("*******************")
