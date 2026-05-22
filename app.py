import streamlit as st
import os
import json
import re
import io
import requests
import pypdf
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# 1. SETUP DE PÁGINA
st.set_page_config(page_title="Curriculator v5.0", page_icon="🤖", layout="centered")

# ═══════════════════════════════════════════════════════════
# CSS CUSTOMIZADO — TEMA PREMIUM E MOBILE FRIENDLY
# ═══════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
    /* Header */
    .app-header {
        background: linear-gradient(135deg, #1a3a5a 0%, #2c5f8a 100%);
        padding: 20px 25px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
        text-align: center;
    }
    .app-header h1 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .app-header p {
        margin: 5px 0 0;
        opacity: 0.8;
        font-size: 0.85rem;
    }

    /* Section headers */
    .section-header {
        color: #1a3a5a;
        font-size: 1.1rem;
        font-weight: 600;
        border-left: 4px solid #1a3a5a;
        padding-left: 12px;
        margin: 20px 0 10px;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 15px;
        font-weight: 600;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Premium
st.markdown(
    """
    <div class="app-header">
        <h1>🤖 Curriculator Exterminador de Negativas</h1>
        <p>Gerador portátil de currículos sob medida para vagas</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════
# INICIALIZAÇÃO DE SESSÃO DO CHATBOT GUPY (ALIA IA)
# ═══════════════════════════════════════════════════════════
if "gupy_mensagens" not in st.session_state:
    st.session_state.gupy_mensagens = [
        {"role": "model", "parts": ["Olá! Eu sou a Alia IA, sua assistente de carreira. Vamos criar um texto estratégico para o campo 'Apresente-se' da Gupy, fugindo do 'copia e cola' do currículo! Para começar, por favor, envie a sua experiência profissional (pode colar o seu currículo)."]}
    ]
if "gupy_step" not in st.session_state:
    st.session_state.gupy_step = 1
if "gupy_resume" not in st.session_state:
    st.session_state.gupy_resume = ""
if "gupy_vacancy" not in st.session_state:
    st.session_state.gupy_vacancy = ""

# ═══════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES E COMPILADORES (SERVICES)
# ═══════════════════════════════════════════════════════════
def extrair_texto_url(url):
    """Extrai texto bruto de uma URL de vaga usando requests e BeautifulSoup."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts, estilos e cabeçalhos/rodapés redundantes
        for element in soup(["script", "style", "header", "footer", "nav", "noscript"]):
            element.decompose()
            
        texto = soup.get_text(separator="\n")
        linhas = (line.strip() for line in texto.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)
    except Exception as e:
        raise Exception(f"Erro ao extrair conteúdo da URL: {e}")

def obter_prompt_extrair_vaga(texto_pag):
    """Prompt para extrair campos essenciais da vaga em JSON."""
    return f"""
    Analise o texto da vaga extraído de uma página web e retorne as seguintes informações estruturadas em formato JSON válido:
    {{
        "empresa": "Nome da empresa contratante (em branco se não identificado)",
        "cargo": "Nome do cargo/função (em branco se não identificado)",
        "descricao": "Resumo geral dos requisitos e responsabilidades da vaga"
    }}
    
    Retorne APENAS o JSON puro, sem marcações ou textos adicionais.
    
    Texto da vaga:
    {texto_pag}
    """

def obter_prompt(canal, empresa, cargo):
    """Prompt para gerar o currículo otimizado no formato JSON."""
    email_part = ""
    if "E-mail" in canal:
        email_part = """
        Além do currículo, preencha também as chaves de e-mail de envio da candidatura:
        - "email_destinatario": Um e-mail de recrutamento sugerido, ex: "vagas@empresa.com" ou "rh@empresa.com".
        - "email_assunto": Um assunto profissional de candidatura para a vaga de {cargo}.
        - "email_corpo": Uma breve carta de apresentação formal em formato de e-mail direcionada ao recrutador.
        """
    else:
        email_part = """
        Deixe as chaves "email_destinatario", "email_assunto" e "email_corpo" como strings vazias.
        """

    return f"""
    Você é um recrutador e especialista em ATS de TI.
    Adapte o currículo base fornecido pelo usuário para a vaga de {cargo} na empresa {empresa}.
    Você deve reescrever o resumo profissional, as atribuições de cada cargo e as habilidades para destacar o fit do candidato com os requisitos da vaga, sem inventar dados que alterem a verdade das experiências reais.
    
    Retorne a resposta estritamente no formato JSON estruturado a seguir:
    {{
        "nome": "Nome completo do candidato",
        "cargo_cabecalho": "{cargo}",
        "contato": {{
            "localizacao": "Cidade - Estado (Ex: São Paulo - SP)",
            "telefone": "Telefone de contato",
            "email": "E-mail de contato",
            "linkedin": "link do perfil do LinkedIn",
            "github": "link do perfil do GitHub (opcional, em branco se não aplicável)"
        }},
        "resumo_profissional": "Resumo otimizado focado nas palavras-chave e competências da vaga (3 a 5 linhas).",
        "experiencia_profissional": [
            {{
                "empresa": "Nome da Empresa",
                "cargo": "Cargo Ocupado",
                "periodo": "Período (Ex: Jan/2022 - Atual)",
                "atribuicoes": [
                    "Atribuição focada em resultados e ferramentas que a vaga pede.",
                    "Outra atribuição importante..."
                ]
            }}
        ],
        "habilidades": [
            "Habilidade 1", "Habilidade 2", ...
        ],
        "educacao": [
            {{
                "curso": "Nome da Formação",
                "instituicao": "Instituição",
                "periodo": "Período (Ex: 2018 - 2022)"
            }}
        ],
        "certificacoes": [
            "Certificação 1", ...
        ],
        "email_destinatario": "",
        "email_assunto": "",
        "email_corpo": ""
    }}
    
    {email_part}
    
    Retorne APENAS o JSON puro. Não escreva explicações nem inclua blocos de markdown.
    """

def gerar_pdf(dados_json, empresa):
    """Compila o currículo a partir do JSON em PDF usando ReportLab em memória."""
    import io
    import re
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib import colors

    def limpar_emojis(texto):
        if not texto:
            return ""
        # Remove caracteres que não estão na faixa Latin-1 (para evitar erros no ReportLab com Helvetica)
        return "".join(c for c in texto if ord(c) < 256)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    name_style = ParagraphStyle(
        'CVName',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1a3a5a'),
        alignment=TA_CENTER,
        spaceAfter=2
    )
    
    sub_style = ParagraphStyle(
        'CVSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#2c5f8a'),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    contact_style = ParagraphStyle(
        'CVContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    section_title_style = ParagraphStyle(
        'CVSectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1a3a5a'),
        spaceBefore=8,
        spaceAfter=2
    )
    
    body_style = ParagraphStyle(
        'CVBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4
    )
    
    bullet_style = ParagraphStyle(
        'CVBullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=2
    )
    
    item_title_style = ParagraphStyle(
        'CVItemTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor('#333333')
    )
    
    item_right_style = ParagraphStyle(
        'CVItemRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#666666'),
        alignment=TA_RIGHT
    )
    
    story = []
    
    # 1. Header (Name, Subtitle, Contact)
    nome = dados_json.get("nome", "Denis Bolfarini")
    story.append(Paragraph(limpar_emojis(nome), name_style))
    
    cargo = dados_json.get("cargo_cabecalho", "")
    if cargo:
        story.append(Paragraph(limpar_emojis(cargo), sub_style))
        
    contato = dados_json.get("contato", {})
    contato_parts = []
    if contato.get("localizacao"):
        contato_parts.append(contato["localizacao"])
    if contato.get("telefone"):
        contato_parts.append(contato["telefone"])
    if contato.get("email"):
        contato_parts.append(contato["email"])
    if contato.get("linkedin"):
        lk = contato["linkedin"].replace("https://www.", "").replace("https://", "")
        contato_parts.append(lk)
    if contato.get("github"):
        gh = contato["github"].replace("https://www.", "").replace("https://", "")
        contato_parts.append(gh)
        
    contact_text = "  |  ".join(contato_parts)
    story.append(Paragraph(limpar_emojis(contact_text), contact_style))
    
    def add_section_header(title):
        story.append(Paragraph(limpar_emojis(title.upper()), section_title_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1a3a5a'), spaceBefore=2, spaceAfter=6))
        
    # 2. Resumo Profissional
    resumo = dados_json.get("resumo_profissional", "")
    if resumo:
        add_section_header("Resumo Profissional")
        story.append(Paragraph(limpar_emojis(resumo), body_style))
        story.append(Spacer(1, 4))
        
    # 3. Experiencia Profissional
    experiencias = dados_json.get("experiencia_profissional", [])
    if experiencias:
        add_section_header("Experiencia Profissional")
        for exp in experiencias:
            emp = exp.get("empresa", "")
            cargo_job = exp.get("cargo", "")
            periodo = exp.get("periodo", "")
            
            left_text = f"<b>{emp}</b> &mdash; {cargo_job}"
            
            col_widths = [360, 160] # Total width 520
            row_data = [
                [Paragraph(limpar_emojis(left_text), item_title_style), Paragraph(limpar_emojis(periodo), item_right_style)]
            ]
            t = Table(row_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ]))
            story.append(t)
            story.append(Spacer(1, 2))
            
            # Attributions
            atribuicoes = exp.get("atribuicoes", [])
            for attr in atribuicoes:
                attr_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', attr)
                story.append(Paragraph(f"&bull; {limpar_emojis(attr_html)}", bullet_style))
            story.append(Spacer(1, 4))
            
    # 4. Habilidades
    habilidades = dados_json.get("habilidades", [])
    if habilidades:
        add_section_header("Habilidades & Competencias")
        habilidade_text = ", ".join(habilidades)
        story.append(Paragraph(limpar_emojis(habilidade_text), body_style))
        story.append(Spacer(1, 4))
        
    # 5. Educacao
    educacao = dados_json.get("educacao", [])
    if educacao:
        add_section_header("Educacao")
        for edu in educacao:
            curso = edu.get("curso", "")
            inst = edu.get("instituicao", "")
            periodo = edu.get("periodo", "")
            
            left_text = f"<b>{curso}</b> &mdash; {inst}"
            
            row_data = [
                [Paragraph(limpar_emojis(left_text), item_title_style), Paragraph(limpar_emojis(periodo), item_right_style)]
            ]
            t = Table(row_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ]))
            story.append(t)
            story.append(Spacer(1, 2))
            
    # 6. Certificacoes
    certificacoes = dados_json.get("certificacoes", [])
    if certificacoes:
        add_section_header("Certificacoes")
        cert_text = ", ".join(certificacoes)
        story.append(Paragraph(limpar_emojis(cert_text), body_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ═══════════════════════════════════════════════════════════
# CONFIGURAÇÃO DE SEGURANÇA E AMBIENTE (SIDEBAR)
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚙️ Configurações")
    
    # 1. Carrega API Key de secrets ou local
    chave_padrao = ""
    try:
        chave_padrao = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    except Exception:
        chave_padrao = os.environ.get("GEMINI_API_KEY", "")

    api_key = st.text_input(
        "Sua Google API Key",
        value=chave_padrao,
        type="password",
        help="Insira sua chave ou configure-a como GEMINI_API_KEY nas configurações de Secrets do Streamlit Cloud."
    )
    
    st.markdown("---")
    st.subheader("📄 Seu Currículo Base")
    opcao_curriculo = st.radio("Origem do currículo base:", ["Carregar PDF", "Colar Texto"], horizontal=True)

    curriculo_texto = ""
    if opcao_curriculo == "Carregar PDF":
        arquivo_pdf = st.file_uploader("Envie seu currículo geral em PDF", type=["pdf"])
        if arquivo_pdf is not None:
            try:
                leitor = pypdf.PdfReader(arquivo_pdf)
                paginas = [pagina.extract_text() for pagina in leitor.pages]
                curriculo_texto = "\n".join(paginas)
                st.success("✅ Currículo PDF carregado!")
            except Exception as e:
                st.error(f"Erro ao ler PDF: {e}")
    else:
        curriculo_texto = st.text_area(
            "Cole seu currículo de referência:",
            height=180,
            placeholder="Cole o histórico profissional completo aqui..."
        )
        
    st.markdown("---")
    if st.button("🗑️ Resetar Chat Gupy", use_container_width=True):
        st.session_state.gupy_mensagens = [
            {"role": "model", "parts": ["Olá! Eu sou a Alia IA, sua assistente de carreira. Vamos criar um texto estratégico para o campo 'Apresente-se' da Gupy, fugindo do 'copia e cola' do currículo! Para começar, por favor, envie a sua experiência profissional (pode colar o seu currículo)."]}
        ]
        st.session_state.gupy_step = 1
        st.session_state.gupy_resume = ""
        st.session_state.gupy_vacancy = ""
        st.success("Chat Gupy resetado com sucesso!")
        st.rerun()

# Trava de Segurança
if not api_key:
    st.warning("👈 Insira sua Google API Key na barra lateral para começar.")
    st.stop()

try:
    cliente = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Erro ao inicializar API do Gemini: {e}")
    st.stop()


# ═══════════════════════════════════════════════════════════
# LAYOUT COM ABAS PRINCIPAIS
# ═══════════════════════════════════════════════════════════
tab_gerador, tab_chatbot = st.tabs(["📄 Gerador de Currículo (PDF)", "💬 Assistente Gupy (Alia IA)"])

# ─────────────────────────────────────────────────────────
# ABA 1: GERADOR DE CURRÍCULO (PDF E E-MAIL)
# ─────────────────────────────────────────────────────────
with tab_gerador:
    st.markdown('<div class="section-header">Preencha os dados da vaga</div>', unsafe_allow_html=True)
    
    # --- Auto-fill via URL ---
    col_url, col_btn = st.columns([4, 1.2])
    url_vaga = col_url.text_input(
        "🔗 URL da Vaga (Gupy ou similar - opcional)",
        placeholder="Cole o link da vaga aqui...",
        key="url_vaga_input"
    )
    buscar_url = col_btn.button("🔍 Autocompletar", use_container_width=True)

    # Session state para campos do formulário
    for key in ["f_empresa", "f_cargo", "f_descricao"]:
        if key not in st.session_state:
            st.session_state[key] = ""

    if buscar_url and url_vaga:
        with st.spinner("🌐 Extraindo e analisando detalhes da vaga..."):
            try:
                texto_pag = extrair_texto_url(url_vaga)
                prompt_ext = obter_prompt_extrair_vaga(texto_pag)
                
                resp_ext = cliente.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt_ext],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                
                raw_json = resp_ext.text.strip()
                # Limpa tags Markdown do JSON se houver
                if raw_json.startswith("```"):
                    raw_json = raw_json.split("```json")[-1].split("```")[0].strip()
                    
                dados_url = json.loads(raw_json)
                st.session_state.f_empresa = dados_url.get("empresa", "")
                st.session_state.f_cargo = dados_url.get("cargo", "")
                st.session_state.f_descricao = dados_url.get("descricao", "")
                st.success("✅ Dados importados com sucesso! Revise e edite abaixo.")
            except Exception as err:
                st.error(f"Erro ao buscar detalhes da URL: {err}")

    # Campos do Formulário
    empresa = st.text_input("Nome da Empresa", value=st.session_state.f_empresa)
    cargo = st.text_input("Cargo Desejado", value=st.session_state.f_cargo)
    texto_vaga = st.text_area("Descrição da Vaga / Requisitos", value=st.session_state.f_descricao, height=150)
    
    canal = st.radio(
        "Canal de Envio:",
        ["E-mail (PDF + Texto de E-mail)", "Currículo (Apenas PDF)"],
        horizontal=True
    )

    # Botão de processamento
    gerar_cv = st.button("🚀 Gerar Currículo Otimizado", use_container_width=True)

    if gerar_cv:
        if not curriculo_texto.strip():
            st.warning("⚠️ Forneça seu Currículo Base na barra lateral primeiro.")
        elif not empresa or not cargo or not texto_vaga:
            st.warning("⚠️ Preencha os campos obrigatórios (Empresa, Cargo e Descrição da Vaga).")
        else:
            with st.status("🧠 Customizando currículo com IA...", expanded=True) as status:
                try:
                    status.write("⚙️ Enviando dados e perfil base ao Gemini...")
                    prompt_opt = obter_prompt(canal, empresa, cargo)
                    
                    resposta = cliente.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[curriculo_texto, prompt_opt, texto_vaga],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    
                    status.write("🎨 Decodificando dados e compilando o layout do PDF...")
                    conteudo_bruto = resposta.text.strip()
                    if conteudo_bruto.startswith("```"):
                        conteudo_bruto = conteudo_bruto.split("```json")[-1].split("```")[0].strip()
                        
                    dados_json = json.loads(conteudo_bruto)
                    
                    # Gera os bytes do PDF
                    pdf_bytes = gerar_pdf(dados_json, empresa)
                    
                    status.update(label="✅ Pipeline concluído com sucesso!", state="complete")
                    
                    # 1-Click Download Button
                    st.success("✨ Seu Currículo Otimizado em PDF está pronto!")
                    st.download_button(
                        label="📥 BAIXAR CURRÍCULO EM PDF",
                        data=pdf_bytes,
                        file_name=f"Curriculo_{empresa.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    # Mostra os dados de e-mail se solicitado
                    if "E-mail" in canal:
                        st.markdown("### 📧 Sugestão de E-mail de Envio")
                        st.text_input("📬 Destinatário sugerido:", value=dados_json.get("email_destinatario", ""))
                        st.text_input("📌 Assunto sugerido:", value=dados_json.get("email_assunto", ""))
                        st.text_area("✉️ Corpo do E-mail (copie):", value=dados_json.get("email_corpo", ""), height=220)
                        
                except Exception as err:
                    st.error(f"Erro no processamento da IA ou na compilação do PDF: {err}")


# ─────────────────────────────────────────────────────────
# ABA 2: ASSISTENTE GUPY (ALIA IA)
# ─────────────────────────────────────────────────────────
with tab_chatbot:
    st.subheader("💬 Assistente Gupy (Alia IA)")
    
    # Container com rolagem para o chat
    container_gupy = st.container(height=400)
    with container_gupy:
        for msg in st.session_state.gupy_mensagens:
            role = "assistant" if msg["role"] == "model" else "user"
            with st.chat_message(role):
                st.markdown(msg["parts"][0])
                
    # Entrada do chat
    if prompt_gupy := st.chat_input("Responda à Alia IA aqui..."):
        # Mostra a mensagem do usuário na tela e salva
        with container_gupy:
            with st.chat_message("user"):
                st.markdown(prompt_gupy)
        st.session_state.gupy_mensagens.append({"role": "user", "parts": [prompt_gupy]})
        
        # Processamento e resposta da Alia IA baseados na etapa do fluxo guiado
        with container_gupy:
            with st.chat_message("assistant"):
                with st.spinner("Alia IA está pensando..."):
                    try:
                        # Etapa 1: Recebeu currículo
                        if st.session_state.gupy_step == 1:
                            st.session_state.gupy_resume = prompt_gupy
                            resposta = "Excelente, recebi sua experiência. Agora, por favor, envie a descrição completa da vaga para a qual você quer se candidatar."
                            st.markdown(resposta)
                            st.session_state.gupy_mensagens.append({"role": "model", "parts": [resposta]})
                            st.session_state.gupy_step = 2
                            st.rerun()
                            
                        # Etapa 2: Recebeu a vaga -> Gera o texto
                        elif st.session_state.gupy_step == 2:
                            st.session_state.gupy_vacancy = prompt_gupy
                            
                            system_instruction = (
                                "A partir de agora, você atuará como \"Alia IA\", uma especialista em carreira e coach de recolocação profissional, especialista no algoritmo e nas boas práticas da plataforma Gupy. Seu tom será encorajador, prático e focado em ajudar o candidato a se destacar.\n\n"
                                "Seu objetivo é gerar um texto de apresentação personalizado e de alto impacto para a seção \"Apresente-se\" de uma vaga de emprego, seguindo uma metodologia estruturada em 3 pilares.\n\n"
                                "Regras de Estrutura do Texto Gerado:\n"
                                "1. O texto deve ter começo, meio e fim, dividido em 3 parágrafos diretos. Escrito em primeira pessoa e tom profissional. PROIBIDO fazer resumo em tópicos.\n"
                                "2. TAMANHO RIGOROSO: O texto final DEVE ter no MÁXIMO 1300 caracteres (incluindo espaços) para garantir margem de segurança e não ser cortado pela Gupy. Seja extremamente conciso e vá direto ao ponto.\n"
                                "3. Parágrafo 1 (Por que essa empresa?): Conecte o atrativo da vaga com a história do candidato.\n"
                                "4. Parágrafo 2 (Por que essa vaga, agora?): Fale sobre a trajetória do candidato conectada ao momento de carreira.\n"
                                "5. Parágrafo 3 (O que entrego de valor?): Cite a experiência do currículo do candidato que prova que ele pode resolver os desafios da vaga.\n\n"
                                "Análise Silenciosa a ser feita:\n"
                                "- Deduza o Atrativo: Leia a vaga e identifique o que a empresa mais valoriza.\n"
                                "- Deduza o Momento de Carreira Exigido: Analise o tom e os requisitos da vaga para definir a persona desejada.\n"
                                "- Cruze os Dados: Encontre no currículo a experiência ou projeto que melhor prova esse fit."
                            )
                            
                            prompt_api = f"""
                            Baseado nas experiências do candidato e na descrição da vaga fornecidas abaixo, gere o texto de apresentação ideal ("Apresente-se") para a Gupy de no MÁXIMO 1300 caracteres.
                            
                            Experiência do Candidato:
                            {st.session_state.gupy_resume}
                            
                            Descrição da Vaga:
                            {st.session_state.gupy_vacancy}
                            
                            Após o texto finalizado, em uma nova linha no final da mensagem, informe a quantidade aproximada de caracteres gerados e pergunte se o candidato gostou do direcionamento.
                            """
                            
                            config = types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.7
                            )
                            
                            resp = cliente.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=[prompt_api],
                                config=config
                            )
                            
                            resposta = resp.text
                            st.markdown(resposta)
                            st.session_state.gupy_mensagens.append({"role": "model", "parts": [resposta]})
                            st.session_state.gupy_step = 3
                            st.rerun()
                            
                        # Etapa 3: Interações/Refinamentos pós-geração
                        elif st.session_state.gupy_step == 3:
                            system_instruction = (
                                "Você é a Alia IA. Continue a conversa com o candidato ajustando o texto gerado de acordo com o feedback dele. "
                                "Lembre-se de manter o tom encorajador e o limite estrito de 1300 caracteres estruturado em 3 parágrafos."
                            )
                            
                            config = types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.7
                            )
                            
                            # Monta contexto
                            contexto = f"Currículo original:\n{st.session_state.gupy_resume}\n\nDescrição da Vaga:\n{st.session_state.gupy_vacancy}\n\nHistórico:\n"
                            for m in st.session_state.gupy_mensagens[:-1]:
                                role_name = "Candidato" if m["role"] == "user" else "Alia IA"
                                contexto += f"{role_name}: {m['parts'][0]}\n"
                                
                            prompt_api = f"{contexto}\nCandidato enviou o seguinte feedback/ajuste: {prompt_gupy}\n\nAlia IA, responda fornecendo a nova versão do texto adaptado com base no feedback e informando a nova contagem de caracteres."
                            
                            resp = cliente.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=[prompt_api],
                                config=config
                            )
                            
                            resposta = resp.text
                            st.markdown(resposta)
                            st.session_state.gupy_mensagens.append({"role": "model", "parts": [resposta]})
                            st.rerun()
                            
                    except Exception as err:
                        st.error(f"Erro ao interagir com a IA: {err}")