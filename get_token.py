import requests
import os

# Dados fornecidos
client_id = '4601797779457193'
client_secret = 'QZq9baSY9Pyl1h8YINmz7WBwga5hoKPi' # Removed < > and newline based on common format, assuming user meant the value inside
code = 'TG-692cb1db0cb9630001f2b41a-71527835'
redirect_uri = 'https://pedicellate-frank-interuniversity.ngrok-free.dev'

url = "https://api.mercadolibre.com/oauth/token"
payload = {
    'grant_type': 'authorization_code',
    'client_id': client_id,
    'client_secret': client_secret,
    'code': code,
    'redirect_uri': redirect_uri
}

print(f"Solicitando token para code: {code}...")

try:
    response = requests.post(url, data=payload)
    response.raise_for_status()
    data = response.json()
    
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    user_id = data.get('user_id')
    
    # Atualizar .env
    env_path = '.env'
    new_lines = []
    
    # Ler linhas existentes mantendo as que não são os tokens do ML
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if not line.strip().startswith('MERCADO_LIVRE_TOKEN=') and \
                   not line.strip().startswith('MERCADO_LIVRE_REFRESH_TOKEN='):
                    new_lines.append(line)
    
    # Garantir que termina com nova linha antes de adicionar novos
    if new_lines and not new_lines[-1].endswith('\n'):
        new_lines[-1] += '\n'
        
    new_lines.append(f"MERCADO_LIVRE_TOKEN={access_token}\n")
    new_lines.append(f"MERCADO_LIVRE_REFRESH_TOKEN={refresh_token}\n")
    
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
        
    print(f"Sucesso! User ID: {user_id}")

except Exception as e:
    print(f"Erro: {e}")
    if 'response' in locals():
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
