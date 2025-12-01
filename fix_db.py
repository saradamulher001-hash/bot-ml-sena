import os
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("Erro: DATABASE_URL não encontrada no .env")
    exit(1)

def fix_database():
    try:
        print("Conectando ao banco de dados...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("Executando alteração na tabela users...")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Banco de dados corrigido!")
    except Exception as e:
        print(f"Erro ao corrigir banco de dados: {e}")

if __name__ == "__main__":
    fix_database()
