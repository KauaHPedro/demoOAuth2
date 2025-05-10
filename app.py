from dotenv import load_dotenv
from flask import Flask, redirect, url_for, session, request, render_template_string
from requests_oauthlib import OAuth2Session
import os

# Carrega variáveis de ambiente de .env
load_dotenv()

# Permite usar HTTP em localhost (não recomendado em produção)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Chave para criptografar sessão

# Configurações do OAuth2
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = 'http://localhost:5000/callback'

# Endpoints do Google
authorization_base_url = 'https://accounts.google.com/o/oauth2/auth'
token_url             = 'https://oauth2.googleapis.com/token'
userinfo_endpoint     = 'https://www.googleapis.com/oauth2/v3/userinfo'

# Escopos de acesso (profile e email)
scope = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email'
]


@app.route('/')
def index():
    """
    Página inicial com botão "Entrar com Google"
    """
    return render_template_string('''
    <html>
        <head>
            <title>Login com Google</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(to right, #667eea, #764ba2);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .login-box {
                    background-color: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    text-align: center;
                }
                .google-btn {
                    display: inline-block;
                    background-color: #4285F4;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: bold;
                    transition: background 0.3s;
                }
                .google-btn:hover {
                    background-color: #357ae8;
                }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h1>Bem-vindo!</h1>
                <a class="google-btn" href="{{ url_for('login') }}">Entrar com Google</a>
            </div>
        </body>
    </html>
    ''')


@app.route('/login')
def login():
    """
    Inicia o fluxo OAuth2:
    - Gera URL de autorização
    - Armazena 'state' na sessão
    - Redireciona usuário para Google
    """
    google = OAuth2Session(
        client_id,
        scope=scope,
        redirect_uri=redirect_uri
    )
    authorization_url, state = google.authorization_url(
        authorization_base_url,
        access_type="offline",
        prompt="select_account"
    )
    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    """
    Recebe o callback do Google:
    - Verifica state
    - Troca authorization code por token (fetch_token)
    - Armazena token na sessão
    - Redireciona para /profile para evitar recarga dupla
    """
    if 'oauth_state' not in session:
        # Se o usuário acessar callback diretamente, redireciona ao login
        return redirect(url_for('login'))

    google = OAuth2Session(
        client_id,
        redirect_uri=redirect_uri,
        state=session['oauth_state']
    )

    # fetch_token deve ser chamado apenas uma vez; daí a necessidade de /profile
    token = google.fetch_token(
        token_url,
        client_secret=client_secret,
        authorization_response=request.url
    )
    session['oauth_token'] = token

    return redirect(url_for('profile'))


@app.route('/profile')
def profile():
    """
    Exibe perfil do usuário:
    - Requer token válido na sessão
    - Faz requisição ao endpoint /userinfo
    """
    if 'oauth_token' not in session:
        return redirect(url_for('login'))

    google = OAuth2Session(
        client_id,
        token=session['oauth_token']
    )
    resp = google.get(userinfo_endpoint)
    user = resp.json()

    # Se os dados vierem incompletos, exibe resposta crua para debug
    if 'name' not in user or 'email' not in user:
        return f"<p>Erro: Dados incompletos. Resposta da API:</p><pre>{user}</pre>"

    # HTML simples inline; substitua por template separado se desejar
    return render_template_string('''
    <html>
    <head>
        <title>Bem-vindo</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(to right, #74ebd5, #ACB6E5);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .welcome-box {
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.15);
                text-align: center;
                max-width: 400px;
            }
            .welcome-box h1 {
                color: #333;
                margin-bottom: 16px;
            }
            .welcome-box p {
                color: #555;
                font-size: 18px;
            }
                                  
            .logout-btn {
                display: inline-block;
                margin-top: 20px;
                padding: 10px 20px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                transition: background 0.3s;
            }
                                  
            .logout-btn:hover {
                background-color: #d32f2f;
            }

        </style>
    </head>
    <body>
        <div class="welcome-box">
            <h1>Olá, {{ user.name }}!</h1>
            <p>Email: {{ user.email }}</p>
            <a href="{{ url_for('logout') }}" class="logout-btn">Deslogar</a>
        </div>
    </body>
    </html>
    ''', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Executa app em modo debug (remova debug=True em produção)
    app.run(debug=True)
