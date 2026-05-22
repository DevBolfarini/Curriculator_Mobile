🤖 Curriculator Agent

O Curriculator Agent é um assistente de carreira inteligente e conversacional (Chatbot) construído com Python, Streamlit e a API do Google Gemini (usando a nova SDK google-genai).

Ele atua como uma Consultora de Carreira Sênior (Alia IA), conversando de forma interativa com o usuário para analisar descrições de vagas e adaptar o seu currículo original (do LinkedIn ou em PDF) para que fique muito mais alinhado com a vaga de interesse, mantendo rigorosamente a mesma formatação e estrutura do currículo original.

✨ O que a aplicação se propõe a fazer?

O Curriculator Agent ajuda na otimização estratégica de currículos com as seguintes propostas de valor:

1. **Leitura Automatizada de Currículos:** Você faz o upload do seu currículo em PDF (exportado do LinkedIn ou gerado localmente) ou cola o texto dele diretamente no painel.
2. **Análise de Vagas Contextual:** Você cola a descrição da vaga desejada diretamente no chat.
3. **Refinamento Ativo:** Se a IA sentir falta de alguma informação crucial que a vaga exige e que não está no seu currículo, ela fará perguntas estratégicas a você antes de gerar o currículo adaptado.
4. **Currículo Otimizado para ATS:** A IA reescreve seu resumo profissional, habilidades e realizações para incluir palavras-chave estratégicas da vaga, mas preservando o estilo de escrita e o layout original.
5. **Cópia em 1 Clique:** O currículo final adaptado é apresentado dentro de um bloco de código Markdown, permitindo que você o copie com formatação completa com apenas um clique.
6. **Portabilidade e Segurança:** Sem bancos de dados ou arquivos `.env`. Sua chave de API fica armazenada apenas na memória temporária da sessão ou configurada de forma segura nos Secrets do Streamlit Cloud.

🛠️ Tecnologias Utilizadas

Linguagem: Python 3.9+

Interface Web: Streamlit

Inteligência Artificial: Google Gemini API (gemini-2.5-flash)

SDK: google-genai (Nova SDK oficial do Google)

🚀 Como instalar e executar localmente

Siga os passos abaixo para rodar a aplicação na sua máquina:

1. Preparando o ambiente

Crie uma pasta para o projeto e adicione os arquivos app.py e requirements.txt.
Abra o terminal nesta pasta.

2. Criando o Ambiente Virtual (Recomendado)

Para não conflitar com outras bibliotecas do seu computador, crie e ative um ambiente virtual:

# Criar ambiente virtual
python -m venv venv

# Ativar no Windows (Prompt de Comando / CMD):
venv\Scripts\activate

# Ativar no Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Ativar no Windows (Git Bash / bash):
source venv/Scripts/activate

# Ativar no Mac/Linux:
source venv/bin/activate


3. Instalando as Dependências

Instale as bibliotecas necessárias listadas no requirements.txt:

pip install -r requirements.txt


4. Iniciando a Aplicação

Com tudo instalado, execute o servidor do Streamlit:

streamlit run app.py


O navegador abrirá automaticamente no endereço http://localhost:8501.


☁️ Como publicar no Streamlit Cloud

Para disponibilizar esta aplicação online e acessá-la de qualquer lugar (computador ou celular):

1. **Suba o código para o GitHub**:
   - Crie um repositório no GitHub.
   - Envie os arquivos app.py, requirements.txt e readme.md para lá. *(Nota: Não envie a pasta `venv`)*.

2. **Conecte ao Streamlit Cloud**:
   - Acesse o [Streamlit Community Cloud](https://share.streamlit.io/).
   - Faça login com sua conta do GitHub.
   - Clique em **"New app"**.

3. **Configure os detalhes de publicação**:
   - **Repository**: Selecione seu repositório criado.
   - **Branch**: Geralmente `main` ou `master`.
   - **Main file path**: Digite `app.py`.
   - Clique em **"Deploy!"**.

4. **(Opcional) Configurar Chave de API como Segredo (Secrets)**:
   - Se você não quiser digitar/colar sua chave toda vez que abrir o aplicativo online, pode salvá-la nos Segredos do Streamlit Cloud.
   - No painel da sua aplicação publicada no Streamlit Cloud, vá em **Settings** > **Secrets**.
   - Adicione sua chave neste formato:
     ```toml
     GEMINI_API_KEY = "sua-chave-api-aqui"
     ```
   - Clique em **Save**. O aplicativo detectará automaticamente a chave e iniciará pronto para o uso.


📖 Como usar a aplicação (Documentação do Usuário)

Obtenha sua Chave API: Acesse o Google AI Studio, faça login e crie uma chave de API gratuita.

Insira a Chave na Aplicação: Com o Curriculator Agent aberto, vá até a barra lateral esquerda (⚙️ Configurações) e cole sua chave no campo "Sua Google API Key". O chat será desbloqueado.

Inicie a Conversa:

Envie uma mensagem como: "Quero me candidatar para esta vaga de Analista de Dados: [cole a vaga]"

Responda às perguntas do Agente.

Peça para ele gerar o texto final para a Gupy ou e-mail.

Limpando a Sessão: Use o botão "🗑️ Limpar Conversa" na barra lateral para apagar a memória do agente e começar uma análise para uma vaga totalmente nova.

🏗️ Documentação Técnica e Arquitetura

O projeto foi construído focado em simplicidade (MVP) e na arquitetura de chat.

Gerenciamento de Estado (st.session_state)

O Streamlit recarrega o script inteiro a cada interação do usuário. Para que o agente seja conversacional, o histórico é armazenado em st.session_state.mensagens.
Este array guarda dicionários no formato exigido pela SDK do Gemini, mapeando role (user/model) e parts (o texto da mensagem).

Integração com o Gemini (google.genai)

O projeto utiliza o método cliente.chats.create(...) que abstrai o envio do histórico.

Modelo: gemini-2.5-flash (escolhido por ser extremamente rápido e eficiente para tarefas de geração de texto e roleplay).

System Instruction: O comportamento do agente é blindado através do parâmetro system_instruction nas configurações da API (types.GenerateContentConfig). Isso garante que a IA não saia do personagem de "Consultor de Carreira".

Segurança

O projeto não faz uso de bibliotecas como python-dotenv. A decisão arquitetural de pedir a chave via st.sidebar.text_input(..., type="password") garante que a aplicação possa ser hospedada publicamente (ex: Streamlit Community Cloud) sem expor credenciais do desenvolvedor. A chave vive apenas no backend temporário enquanto a aba do navegador estiver aberta.

Desenvolvido com 💻 e IA para acelerar sua recolocação profissional.