import streamlit as st
from google import genai
from google.genai import types

# 1. Configuração da Página
st.set_page_config(page_title="Curriculator Agent", page_icon="🤖", layout="centered")

# 2. Inicialização da Memória (Session State)
# Isso garante que a IA lembre do que vocês estão conversando
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {"role": "model", "parts": ["Olá, Denis! Sou seu Consultor de Carreira Sênior. Cole a descrição da vaga aqui ou me conte o que você está buscando para começarmos a alinhar seu perfil."]}
    ]

# 3. Sidebar: Configuração Segura (Sem .env)
with st.sidebar:
    st.title("⚙️ Configurações")
    st.markdown("Para garantir sua segurança e portabilidade, não usamos arquivos `.env`.")
    
    # Tenta obter a chave do st.secrets ou os.environ (útil para o Streamlit Cloud)
    import os
    chave_padrao = ""
    try:
        chave_padrao = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    except Exception:
        chave_padrao = os.environ.get("GEMINI_API_KEY", "")

    # Recebe a chave como senha (inicia preenchida se configurada nos Secrets)
    api_key = st.text_input(
        "Sua Google API Key",
        value=chave_padrao,
        type="password",
        help="Insira sua chave para ativar o agente ou configure GEMINI_API_KEY nas configurações de Secrets do Streamlit."
    )
    
    st.markdown("---")
    st.markdown("🔒 *Sua chave fica armazenada apenas na memória temporária enquanto a aba estiver aberta.*")
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.mensagens = [
            {"role": "model", "parts": ["Olá, Denis! Sou seu Consultor de Carreira Sênior. Cole a descrição da vaga aqui ou me conte o que você está buscando para começarmos a alinhar seu perfil."]}
        ]
        st.rerun()

# 4. Interface Principal
st.title("🤖 Curriculator Agent")
st.markdown("Seu assistente estratégico para análise de vagas e criação de cartas de apresentação.")
st.divider()

# Trava de Segurança: Se não tem chave, não deixa usar o chat
if not api_key:
    st.warning("👈 Por favor, insira sua Google API Key na barra lateral para habilitar o chat.")
    st.stop()

# Inicializa o cliente do Gemini
try:
    cliente = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Erro ao inicializar o cliente: {e}")
    st.stop()

# 5. Renderiza o histórico do Chat na tela
for msg in st.session_state.mensagens:
    # Ajusta o nome do 'role' para o Streamlit (model -> assistant)
    role = "assistant" if msg["role"] == "model" else "user"
    with st.chat_message(role):
        st.markdown(msg["parts"][0])

# 6. Interação do Usuário (Chat Input)
if prompt_usuario := st.chat_input("Digite sua mensagem aqui..."):
    
    # 6.1 Exibe a mensagem do usuário na tela e salva no histórico
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    st.session_state.mensagens.append({"role": "user", "parts": [prompt_usuario]})

    # 6.2 Chama a IA e exibe a resposta
    with st.chat_message("assistant"):
        with st.spinner("Analisando..."):
            try:
                # Instrução de Sistema (Persona do Agente)
                config = types.GenerateContentConfig(
                    system_instruction=(
                        "Você é a Alia IA, uma Consultora de Carreira Sênior ajudando Denis Bolfarini a se recolocar. "
                        "Seu objetivo é conversar com ele, analisar vagas e redigir textos persuasivos para candidaturas "
                        "(como o 'Apresente-se' da Gupy ou e-mails corporativos). "
                        "Você é empática, estratégica e direta ao ponto. Se ele te mandar uma vaga, identifique as palavras-chave "
                        "e, se sentir falta de alguma informação do histórico dele para bater com a vaga, faça UMA pergunta específica "
                        "para ele antes de redigir o texto final."
                    ),
                    temperature=0.7
                )
                
                # Monta o histórico no formato exigido pela SDK do Gemini
                historico_api = []
                # Pega todas as mensagens, exceto a primeira (boas-vindas do model) e a última que o usuário acabou de enviar
                # A API do Gemini exige que o histórico comece com uma mensagem do usuário ('user')
                for m in st.session_state.mensagens[1:-1]:
                     historico_api.append(
                          types.Content(role=m["role"], parts=[types.Part.from_text(text=m["parts"][0])])
                     )

                # Cria a sessão de chat contínuo
                chat = cliente.chats.create(
                    model="gemini-2.5-flash",
                    config=config,
                    history=historico_api
                )

                # Envia a nova mensagem do usuário para o chat
                resposta = chat.send_message(prompt_usuario)
                texto_resposta = resposta.text

                # Exibe a resposta na tela
                st.markdown(texto_resposta)
                
                # Salva a resposta da IA no histórico local
                st.session_state.mensagens.append({"role": "model", "parts": [texto_resposta]})
                
            except Exception as err:
                st.error(f"Ocorreu um erro ao comunicar com a IA: {err}")