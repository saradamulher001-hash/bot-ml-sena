from flask import Flask, request, jsonify, redirect, render_template_string, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from dotenv import load_dotenv
import requests
import os
from openai import OpenAI
from sqlalchemy import text

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua_chave_secreta_super_segura') # Necessário para sessões
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar Extensões
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Modelos ---

# Modelo do Cliente SaaS (Tabela 'users' no Banco)
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.BigInteger, primary_key=True)
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<User {self.user_id}>'

# Modelo do Administrador (Para Login)
class AdminUser(UserMixin):
    id = 1

@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':
        return AdminUser()
    return None

# --- Admin Views ---

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class UserModelView(ModelView):
    column_list = ('user_id', 'is_active', 'access_token')
    form_columns = ('user_id', 'is_active', 'access_token', 'refresh_token')
    can_create = False # Geralmente criado via OAuth
    can_delete = True
    can_edit = True
    
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

admin = Admin(app, name='Bot SaaS Admin', index_view=MyAdminIndexView())
admin.add_view(UserModelView(User, db.session))

# --- Banco de Dados (Migração e Init) ---

def init_db():
    with app.app_context():
        # Cria tabelas se não existirem
        db.create_all()
        
        # Migração Manual: Adicionar coluna is_active se não existir
        try:
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            if 'is_active' not in columns:
                print("Migrando banco de dados: Adicionando coluna 'is_active'...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                    conn.commit()
                print("Migração concluída.")
        except Exception as e:
            print(f"Erro na verificação/migração do banco: {e}")

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
    return 'Bot SaaS Multi-Tenant (PostgreSQL + Admin) Online'

# Rota de Login do Admin
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Hardcoded Admin Credentials
        if username == 'admin' and password == 'suasenha123':
            user = AdminUser()
            login_user(user)
            return redirect(url_for('admin.index'))
        else:
            return "Login falhou. Verifique suas credenciais."
            
    return '''
        <form method="post">
            <p><input type=text name=username placeholder="Usuário">
            <p><input type=password name=password placeholder="Senha">
            <p><input type=submit value=Login>
        </form>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/install', methods=['GET'])
def install():
    # Hardcoded credentials as requested to avoid NoneType error
    client_id = '4601797779457193'
    redirect_uri = 'https://bot-mercadolivre.onrender.com/callback'
    
    auth_url = f"https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
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
        # Fallback para o hardcoded se env falhar, para manter consistência com /install
        CLIENT_ID = '4601797779457193'

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
        
        # Salvar usando SQLAlchemy
        user = User.query.get(user_id)
        if not user:
            user = User(user_id=user_id)
        
        user.access_token = access_token
        user.refresh_token = refresh_token
        # is_active já é True por padrão
        
        db.session.add(user)
        db.session.commit()
        
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
        
        # Buscar usuário no Banco (SQLAlchemy)
        user = User.query.get(user_id)
        
        if not user:
            print(f"Ignorando: Token não encontrado para o usuário {user_id}")
            return jsonify({'status': 'ignored', 'reason': 'user_not_found'}), 200
        
        # --- REGRA DE NEGÓCIO: Verificar se está ativo ---
        if not user.is_active:
            print(f"Ignorando: Usuário {user_id} está INATIVO.")
            return jsonify({'status': 'ignored', 'reason': 'user_inactive'}), 200
            
        token = user.access_token
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
