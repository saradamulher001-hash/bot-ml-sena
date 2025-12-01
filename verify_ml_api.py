import requests
from unittest.mock import MagicMock
from app import obter_pergunta_ml

# Mock requests.get
original_get = requests.get
requests.get = MagicMock()

# Mock response data
mock_response = MagicMock()
mock_response.status_code = 200
mock_response.json.return_value = {
    'status': 'UNANSWERED',
    'text': 'Is this available?',
    'item_id': 'MLB12345678'
}
requests.get.return_value = mock_response

# Test the function
print("Testing obter_pergunta_ml...")
result = obter_pergunta_ml('/questions/123')

if result and result['text'] == 'Is this available?' and result['item_id'] == 'MLB12345678':
    print("SUCCESS: Function returned correct data.")
else:
    print(f"FAILURE: Unexpected result: {result}")

# Restore requests.get
requests.get = original_get
