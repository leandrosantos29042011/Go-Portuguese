from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def home():
    # Cole aqui o código HTML completo do seu jogo ou coloque-o num ficheiro index.html
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>GO PORTUGUESE!</title>
        <!-- Coloque aqui todo o código HTML/JS do seu jogo -->
    </head>
    <body>
        <h1>Meu Jogo está a funcionar no Render!</h1>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
