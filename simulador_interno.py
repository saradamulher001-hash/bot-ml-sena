import sqlite3
import requests
import os
from dotenv import load_dotenv
from app import gerar_resposta_ia

# Carregar variáveis de ambiente (para garantir que a OpenAI Key esteja disponível se app não carregar)
load_dotenv()

def get_token(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT access_token FROM users WHERE user_id = ?', (str(user_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def obter_item_ml(item_id, token):
    url = f"https://api.mercadolibre.com/items/{item_id}"
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return {
            'title': data.get('title'),
            'price': data.get('price'),
            'currency_id': data.get('currency_id'),
            'permalink': data.get('permalink')
        }
    except Exception as e:
        print(f"Erro ao obter item: {e}")
        return None

# 1. Recuperar Token
user_id = '71527835'
token = get_token(user_id)

if not token:
    print(f"Erro: Token não encontrado para o usuário {user_id}")
    exit()

print(f"Token recuperado com sucesso para User {user_id}")

# 2. Consultar Produto
item_id = 'MLB5988627540'
print(f"\nConsultando item {item_id}...")
item_info = obter_item_ml(item_id, token)

if item_info:
    print(f"Produto: {item_info['title']}")
    print(f"Preço: {item_info['currency_id']} {item_info['price']}")
else:
    print("Erro ao consultar produto.")
    exit()

# 3. Simular Pergunta e Gerar Resposta
pergunta = 'Olá! A ponta dela é fina ou média? Serve para desenho?'
print(f"\nPergunta Simulada: '{pergunta}'")

print("Gerando resposta com IA...")
resposta = gerar_resposta_ia(pergunta, item_info)

print(f"\n--- Resposta Final da IA ---\n{resposta}\n----------------------------")
