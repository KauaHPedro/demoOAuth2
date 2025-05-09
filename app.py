from dotenv import load_dotenv
load_dotenv()
from flask import Flask, redirect, url_for, session, request
from requests_oauthlib import OAuth2Session
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = 'http://localhost:5000/callback'
authorization_base_url = 'https://accounts.google.com/o/oauth2/auth'
token_url = 'https://accounts.google.com/o/oauth2/token'
scope = ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']
userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'


@app.route('/')
def index():
    return '''
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
                .login-box h1 {
                    margin-bottom: 20px;
                    color: #333;
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
                <a class="google-btn" href="/login">Entrar com Google</a>
            </div>
        </body>
    </html>
    '''

@app.route('/login')
def login():
    google = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = google.authorization_url(authorization_base_url, access_type="offline", prompt="select_account")
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    if 'oauth_state' not in session:
        return redirect('/login')  # Redireciona corretamente se o fluxo foi quebrado

    google = OAuth2Session(client_id, redirect_uri=redirect_uri, state=session['oauth_state'])
    token = google.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url)
    session['oauth_token'] = token

    userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    resp = google.get(userinfo_url)
    user_info = resp.json()

    if 'name' not in user_info or 'email' not in user_info:
        return f"<p>Erro: Dados incompletos. Resposta da API:</p><pre>{user_info}</pre>"

    return f'''
<html>
<head>
    <title>Bem-vindo</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(to right, #74ebd5, #ACB6E5);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }}
        .welcome-box {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            text-align: center;
            max-width: 400px;
        }}
        .welcome-box h1 {{
            color: #333;
            margin-bottom: 16px;
        }}
        .welcome-box p {{
            color: #555;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="welcome-box">
        <h1>Olá, {user_info['name']}!</h1>
        <p>Email: {user_info['email']}</p>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
