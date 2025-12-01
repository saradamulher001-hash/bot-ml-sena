from unittest.mock import MagicMock
import os

# Mock OpenAI before importing app
mock_client = MagicMock()
mock_completion = MagicMock()
mock_completion.choices = [MagicMock(message=MagicMock(content="Olá! Sim, temos disponível."))]
mock_client.chat.completions.create.return_value = mock_completion

# Patch OpenAI in app
import app
app.client = mock_client

# Test the function
print("Testing gerar_resposta_ia...")
resposta = app.gerar_resposta_ia("Tem disponível?")

if resposta == "Olá! Sim, temos disponível.":
    print("SUCCESS: AI function returned correct response.")
else:
    print(f"FAILURE: Unexpected response: {resposta}")
