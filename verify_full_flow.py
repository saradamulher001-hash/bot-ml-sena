from unittest.mock import MagicMock
import requests
import os

# Mock OpenAI
mock_client = MagicMock()
mock_completion = MagicMock()
mock_completion.choices = [MagicMock(message=MagicMock(content="Resposta IA simulada."))]
mock_client.chat.completions.create.return_value = mock_completion

# Mock requests
original_get = requests.get
original_post = requests.post
requests.get = MagicMock()
requests.post = MagicMock()

# Setup requests mocks
mock_get_response = MagicMock()
mock_get_response.status_code = 200
mock_get_response.json.return_value = {
    'status': 'UNANSWERED',
    'text': 'Pergunta teste',
    'item_id': 'MLB123'
}
requests.get.return_value = mock_get_response

mock_post_response = MagicMock()
mock_post_response.status_code = 200
requests.post.return_value = mock_post_response

# Patch app
import app
app.client = mock_client

# Test notifications route logic directly (simulating the route handler logic)
print("Testing full flow logic...")

# Simulate receiving a webhook
resource = "/questions/12345"
pergunta = app.obter_pergunta_ml(resource)

if pergunta:
    print(f"Pergunta obtida: {pergunta['text']}")
    question_id = resource.split('/')[-1]
    resposta_ia = app.gerar_resposta_ia(pergunta['text'])
    print(f"Resposta IA gerada: {resposta_ia}")
    
    sucesso = app.enviar_resposta_ml(question_id, resposta_ia)
    if sucesso:
        print("SUCCESS: Full flow executed correctly.")
    else:
        print("FAILURE: Failed to send response.")
else:
    print("FAILURE: Failed to get question.")

# Verify calls
requests.get.assert_called()
mock_client.chat.completions.create.assert_called()
requests.post.assert_called()

# Restore mocks
requests.get = original_get
requests.post = original_post
