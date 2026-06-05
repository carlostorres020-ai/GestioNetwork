cat <<EOF > test_login.py
import requests

url = "http://localhost:1035/api/v1/auth/login"
params = {"empresa_id": "ac94f9c4-32b1-484f-8cfa-9d34b6af1c17"}
data = {"username": "admin_gtrack", "password": "admin123"}

response = requests.post(url, params=params, data=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
EOF
