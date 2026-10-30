# 🚀 GO PORTUGUESE! — Jogo Educativo Estilo Kahoot (Multiplayer Online)

Um jogo interativo e multiplayer para sala de aula focado em Língua Portuguesa (ortografia, pontuação, acentuação, concordância e gramática), inspirado na dinâmica do **Kahoot**, com criação personalizada de avatares animados, sintetizador de efeitos sonoros em tempo real, painel de controle do professor e pódio animado com celebração de confetes.

---

## 📁 Estrutura de Arquivos

- **`main.py`**: Servidor e API FastAPI (gerencia salas, alunos conectados, status em tempo real, atualização de pontuação e serve a interface do jogo).
- **`index.html`** / **`go_portuguese.html`**: Interface completa do jogo (Single Page Application com TailwindCSS, avatares SVG em camadas, som sintetizado por Web Audio API, gabarito pedagógico e sincronização online via API e BroadcastChannel).
- **`render.yaml`**: Arquivo de implantação automática (Blueprint) pronto para o **Render**.
- **`requirements.txt`**: Dependências Python (`fastapi`, `uvicorn`, `pydantic`, `gunicorn`).

---

## 🎮 Como Funciona a Partida

1. **Professor**:
   - Clica no botão **Professor** no topo.
   - Digita a senha/PIN de professor (o padrão é `adm@437` ou o configurado na variável de ambiente `TEACHER_PIN`).
   - Clica em **Criar Nova Porta** para gerar um código de 5 dígitos (ex: `84920`).
   - Passa o código para a turma. O painel mostra em tempo real quantos alunos já entraram.
   - Quando todos estiverem prontos, clica em **Iniciar Jogo Agora**.

2. **Alunos**:
   - Criam e personalizam seus avatares (tom de pele, cabelo, roupas, acessórios e auras) e digitam seus nomes.
   - Digitam o código de 5 dígitos da sala e clicam em **Entrar no Saguão**.
   - No saguão, veem todos os colegas que já entraram.
   - Assim que o professor inicia a partida, as telas de todos os alunos iniciam simultaneamente o quiz de 10 perguntas.

3. **Pódio e Gabarito**:
   - A cada resposta correta, os alunos ganham pontos com efeitos visuais e sonoros imediatos.
   - Ao final, todos os resultados são consolidados no **Pódio dos Campeões (1º, 2º e 3º lugar)** e na **Classificação da Turma (Top 10)**.
   - Alunos e professor podem conferir o **Gabarito Pedagógico Completo** com justificativas detalhadas de cada questão.
   - O professor pode **Exportar Relatório CSV** das notas da turma diretamente pelo painel.

---

## ☁️ Como Rodar no Render

### Método 1: Implantação Automática via Blueprint (Recomendado)
1. Conecte seu repositório GitHub ao **Render** ([dashboard.render.com](https://dashboard.render.com)).
2. Clique em **New +** e selecione **Blueprint**.
3. Selecione o repositório **Go-Portuguese**.
4. O Render detectará automaticamente o arquivo `render.yaml` e configurará o Web Service com Python, comando de build, comando de inicialização e checagem de integridade (`/api/health`).
5. Clique em **Apply**. O Render iniciará a compilação e disponibilizará sua URL pública (ex: `https://go-portuguese.onrender.com`).

### Método 2: Web Service Manual no Render
Caso prefira criar manualmente:
1. No Render, clique em **New +** > **Web Service**.
2. Conecte seu repositório.
3. Configure os campos:
   - **Name**: `go-portuguese`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT main:app`
   - **Plan Type**: `Free`
4. Em **Environment Variables**, adicione (opcional):
   - `TEACHER_PIN`: Senha do professor (padrão: `adm@437` se omitido).
   - `PYTHON_VERSION`: `3.11.9`
5. Clique em **Deploy Web Service**.

Ao abrir a URL gerada pelo Render, o jogo carregará diretamente e estará 100% online para qualquer celular, tablet ou computador!

---

## 💻 Como Rodar Localmente

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o servidor:
   ```bash
   python main.py
   ```
   Ou via uvicorn:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. Acesse `http://localhost:8000` no seu navegador.
