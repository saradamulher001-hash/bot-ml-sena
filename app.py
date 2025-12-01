from flask import Flask, request, jsonify, redirect
from dotenv import load_dotenv
import requests
import os
import psycopg2
from openai import OpenAI

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configurações
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ML_APP_ID = os.getenv('ML_APP_ID')
ML_CLIENT_SECRET = os.getenv('ML_CLIENT_SECRET')
ML_REDIRECT_URI = os.getenv('ML_REDIRECT_URI', 'https://bot-mercadolivre.onrender.com/callback')
DATABASE_URL = os.getenv('DATABASE_URL')

# Inicializar cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Banco de Dados (PostgreSQL) ---

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                access_token TEXT,
                refresh_token TEXT
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("Banco de dados (PostgreSQL) inicializado/verificado.")
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")

def save_user(user_id, access_token, refresh_token):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, access_token, refresh_token)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token
        ''', (user_id, access_token, refresh_token))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Usuário {user_id} salvo/atualizado no PostgreSQL.")
    except Exception as e:
        print(f"Erro ao salvar usuário: {e}")

def get_user_token(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT access_token FROM users WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row[0]
        return None
    except Exception as e:
        print(f"Erro ao recuperar token: {e}")
        return None

# --- Funções Auxiliares ML ---

def obter_pergunta_ml(resource_url, token):
    url = f"https://api.mercadolibre.com{resource_url}"
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao obter pergunta: {e}")
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

def enviar_resposta_ml(question_id, texto_resposta, token):
    url = "https://api.mercadolibre.com/answers"
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'question_id': question_id,
        'text': texto_resposta
    }
    
    try:
        print(f"Enviando resposta para {question_id}...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("Resposta enviada com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao enviar resposta: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Detalhes do erro: {e.response.text}")
        return False

def gerar_resposta_ia(pergunta_texto, item_info):
    try:
        contexto_produto = f"Produto: {item_info['title']}\nPreço: {item_info['currency_id']} {item_info['price']}"
        prompt_sistema = "Você é um vendedor prestativo. Responda a pergunta sobre o produto de forma curta e persuasiva em PT-BR."
        prompt_usuario = f"{contexto_produto}\n\nPergunta do cliente: {pergunta_texto}"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro na IA: {e}")
        return "Olá! Em breve responderemos sua pergunta."

# --- Rotas ---

@app.route('/', methods=['GET'])
def home():
    return 'Bot SaaS Multi-Tenant (PostgreSQL) Online'

@app.route('/install', methods=['GET'])
def install():
    auth_url = f"https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={ML_APP_ID}&redirect_uri={ML_REDIRECT_URI}"
    return redirect(auth_url)

@app.route('/callback', methods=['GET'])
def callback():
    code = request.args.get('code')
    if not code:
        return "Erro: Código não fornecido.", 400
    
    # Robustez nas Variáveis
    CLIENT_ID = os.getenv('CLIENT_ID')
    if not CLIENT_ID:
        CLIENT_ID = os.getenv('APP_ID')
    
    if not CLIENT_ID:
        print("Erro Crítico: CLIENT_ID/APP_ID não definido.")
        return "Erro interno: Configuração de Client ID ausente.", 500

    # Tenta obter o secret de várias formas para garantir
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    if not CLIENT_SECRET:
        CLIENT_SECRET = os.getenv('ML_CLIENT_SECRET')

    redirect_uri = 'https://bot-mercadolivre.onrender.com/callback'

    # Debug Logs
    print(f"Tentando login com Client ID: {CLIENT_ID} e Redirect: {redirect_uri}")
    
    # Trocar code por token
    url = "https://api.mercadolibre.com/oauth/token"
    
    # Payload Explícito
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        response_data = response.json()
        
        access_token = response_data.get('access_token')
        refresh_token = response_data.get('refresh_token')
        user_id = response_data.get('user_id')
        
        save_user(user_id, access_token, refresh_token)
        
        return f"Instalação concluída com sucesso! User ID: {user_id}"
    except Exception as e:
        print(f"Erro no callback: {e}")
        if 'response' in locals() and response is not None:
             print(f"Response Body: {response.text}")
             return f"Erro ao obter token: {response.text}", 500
        return f"Erro interno: {e}", 500

@app.route('/notifications', methods=['POST'])
def notifications():
    data = request.get_json()
    topic = data.get('topic')
    user_id = data.get('user_id')
    
    if topic == 'questions':
        print(f"\n--- Notificação para User {user_id} ---")
        
        # Buscar token do usuário
        token = get_user_token(user_id)
        if not token:
            print(f"Ignorando: Token não encontrado para o usuário {user_id}")
            return jsonify({'status': 'ignored', 'reason': 'user_not_found'}), 200
            
        resource = data.get('resource')
        
        # 1. Buscar pergunta
        pergunta = obter_pergunta_ml(resource, token)
        if not pergunta:
            return jsonify({'status': 'error'}), 200
            
        question_id = pergunta.get('id')
        status = pergunta.get('status')
        text = pergunta.get('text')
        item_id = pergunta.get('item_id')
        from_id = pergunta.get('from', {}).get('id')
        
        print(f"Pergunta: '{text}' | Status: {status}")
        
        # 2. Verificações
        if status != 'UNANSWERED':
            print("Ignorando: Não está pendente.")
            return jsonify({'status': 'ignored'}), 200
            
        if str(from_id) == str(user_id):
            print("Ignorando: Auto-pergunta.")
            return jsonify({'status': 'ignored'}), 200
            
        # 3. Buscar Item
        item_info = obter_item_ml(item_id, token)
        if not item_info:
            return jsonify({'status': 'error'}), 200
            
        # 4. Gerar IA
        resposta_ia = gerar_resposta_ia(text, item_info)
        print(f"Resposta IA: {resposta_ia}")
        
        # 5. Enviar
        enviar_resposta_ml(question_id, resposta_ia, token)
        
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    init_db()
    app.run(port=5000)
