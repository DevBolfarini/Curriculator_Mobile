import streamlit as st
from google import genai
from google.genai import types

# 1. Configuração da Página e Funções Auxiliares
st.set_page_config(page_title="Curriculator Agent", page_icon="🤖", layout="wide")

def markdown_to_pdf(md_text):
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
    
    title_style = ParagraphStyle(
        'CVTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1a3a5a'),
        alignment=TA_CENTER,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
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
    
    h2_style = ParagraphStyle(
        'CVH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1a3a5a'),
        spaceBefore=10,
        spaceAfter=4
    )

    h3_style = ParagraphStyle(
        'CVH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#333333'),
        spaceBefore=6,
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
        leading=13,
        textColor=colors.HexColor('#333333')
    )
    
    item_right_style = ParagraphStyle(
        'CVItemRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#666666'),
        alignment=TA_RIGHT
    )

    story = []
    
    linhas = md_text.split('\n')
    is_header_section = True
    
    for linha in linhas:
        linha_limpa = linha.strip()
        if not linha_limpa:
            continue
            
        # Detecta quando saímos do cabeçalho principal
        if linha_limpa.startswith('## '):
            is_header_section = False
            
        # Limpa emojis e caracteres não-latin1
        linha_limpa = limpar_emojis(linha_limpa)
        if not linha_limpa:
            continue
            
        # Processa tags de negrito e itálico do markdown
        linha_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', linha_limpa)
        linha_html = re.sub(r'\*(.*?)\*', r'<i>\1</i>', linha_html)
        
        # Cabeçalho Principal (antes do primeiro H2)
        if is_header_section:
            if linha_limpa.startswith('# '):
                story.append(Paragraph(linha_html[2:].strip(), title_style))
            elif linha_limpa.startswith('### '):
                story.append(Paragraph(linha_html[4:].strip(), subtitle_style))
            else:
                # Trata como informações de contato
                contato_texto = linha_html
                # Remove marcadores de bullet do início se a IA colocou por engano
                if contato_texto.startswith(('* ', '- ')):
                    contato_texto = contato_texto[2:]
                story.append(Paragraph(contato_texto.strip(), contact_style))
            continue
            
        # Corpo do Currículo
        if linha_limpa.startswith('## '):
            story.append(Paragraph(linha_html[3:].strip(), h2_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1a3a5a'), spaceBefore=2, spaceAfter=8))
        elif linha_limpa.startswith('### '):
            texto_h3 = linha_html[4:].strip()
            # Tenta dividir a linha de experiência/curso por separadores comuns
            partes = None
            for sep in [' | ', ' — ', ' - ']:
                if sep in texto_h3:
                    partes = [p.strip() for p in texto_h3.split(sep)]
                    break
            
            if partes and len(partes) >= 2:
                if len(partes) == 3:
                    # Empresa | Cargo | Período
                    left_text = f"<b>{partes[0]}</b> &mdash; {partes[1]}"
                    right_text = partes[2]
                else:
                    # Empresa | Período ou Cargo | Período
                    left_text = f"<b>{partes[0]}</b>"
                    right_text = partes[1]
                
                # Renderiza usando tabela sem bordas alinhada à esquerda e à direita
                row_data = [
                    [Paragraph(left_text, item_title_style), Paragraph(right_text, item_right_style)]
                ]
                t = Table(row_data, colWidths=[360, 160]) # total 520 para A4
                t.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ]))
                story.append(t)
            else:
                story.append(Paragraph(texto_h3, h3_style))
        elif linha_limpa.startswith(('* ', '- ')):
            texto_bullet = f"&bull; {linha_html[2:].strip()}"
            story.append(Paragraph(texto_bullet, bullet_style))
        else:
            story.append(Paragraph(linha_html, body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


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
    
    # Seção para carregar ou colar o currículo
    st.markdown("---")
    st.subheader("📄 Seu Currículo")
    opcao_curriculo = st.radio("Como deseja fornecer seu currículo?", ["Carregar PDF", "Colar Texto"], horizontal=True)

    curriculo_texto = ""
    if opcao_curriculo == "Carregar PDF":
        arquivo_pdf = st.file_uploader("Envie seu currículo em PDF", type=["pdf"])
        if arquivo_pdf is not None:
            try:
                import pypdf
                leitor = pypdf.PdfReader(arquivo_pdf)
                paginas = [pagina.extract_text() for pagina in leitor.pages]
                curriculo_texto = "\n".join(paginas)
                st.success("✅ Currículo carregado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao ler o PDF: {e}")
    else:
        curriculo_texto = st.text_area(
            "Cole o texto do seu currículo aqui",
            height=200,
            placeholder="Cole aqui seu histórico profissional (experiências, habilidades, etc.)..."
        )
        
    st.markdown("---")
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.mensagens = [
            {"role": "model", "parts": ["Olá, Denis! Sou seu Consultor de Carreira Sênior. Cole a descrição da vaga aqui ou me conte o que você está buscando para começarmos a alinhar seu perfil."]}
        ]
        st.rerun()

# 4. Interface Principal
st.title("🤖 Curriculator Agent")
st.markdown("Seu assistente estratégico para adaptar currículos de forma rápida e alinhada com as vagas de interesse.")
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

# Configura colunas lado a lado
col_chat, col_resume = st.columns([1, 1], gap="large")

with col_chat:
    st.subheader("💬 Conversa com Alia IA")
    
    # Container com barra de rolagem para o chat
    container_chat = st.container(height=500)
    with container_chat:
        for msg in st.session_state.mensagens:
            # Ajusta o nome do 'role' para o Streamlit (model -> assistant)
            role = "assistant" if msg["role"] == "model" else "user"
            with st.chat_message(role):
                st.markdown(msg["parts"][0])

with col_resume:
    st.subheader("📄 Currículo Otimizado")
    
    # Tenta extrair o último currículo gerado do histórico
    ultimo_curriculo = ""
    for m in reversed(st.session_state.mensagens):
        if m["role"] == "model":
            texto = m["parts"][0]
            if "```markdown" in texto:
                partes = texto.split("```markdown")
                if len(partes) > 1:
                    ultimo_curriculo = partes[1].split("```")[0].strip()
                    break
            elif "##" in texto:
                ultimo_curriculo = texto.strip()
                break

    # Salva no session_state para permitir edição sem perder a referência ao interagir
    if "curriculo_editado" not in st.session_state:
        st.session_state.curriculo_editado = "O currículo adaptado e otimizado aparecerá nesta área após ser gerado no chat. Você poderá editar o texto diretamente aqui antes de fazer o download do PDF."
        st.session_state.ultimo_curriculo_detectado = ""
        
    if ultimo_curriculo and (st.session_state.get("ultimo_curriculo_detectado") != ultimo_curriculo):
        st.session_state.curriculo_editado = ultimo_curriculo
        st.session_state.ultimo_curriculo_detectado = ultimo_curriculo

    # Editor de texto para refinamento manual
    curriculo_final = st.text_area(
        "Edite o currículo gerado se desejar fazer pequenos ajustes de datas, dados de contato, etc.:",
        value=st.session_state.curriculo_editado,
        height=400,
        key="editor_curriculo"
    )
    # Atualiza o estado da edição
    st.session_state.curriculo_editado = curriculo_final

    # Botões de Download
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.session_state.curriculo_editado and "aparecerá nesta área" not in st.session_state.curriculo_editado:
            try:
                pdf_bytes = markdown_to_pdf(st.session_state.curriculo_editado)
                st.download_button(
                    label="📥 Baixar em PDF",
                    data=pdf_bytes,
                    file_name="Curriculo_Otimizado.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
        else:
            st.button("📥 Baixar em PDF", disabled=True, use_container_width=True, help="Ficará disponível após gerar o currículo no chat.")
            
    with col_d2:
        if st.session_state.curriculo_editado and "aparecerá nesta área" not in st.session_state.curriculo_editado:
            st.download_button(
                label="📝 Baixar em Markdown",
                data=st.session_state.curriculo_editado,
                file_name="Curriculo_Otimizado.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.button("📝 Baixar em Markdown", disabled=True, use_container_width=True, help="Ficará disponível após gerar o currículo no chat.")

# 6. Interação do Usuário (Chat Input)
if prompt_usuario := st.chat_input("Cole a descrição da vaga ou digite sua mensagem aqui..."):
    
    # 6.1 Exibe a mensagem do usuário no container do chat e salva no histórico
    with container_chat:
        with st.chat_message("user"):
            st.markdown(prompt_usuario)
    st.session_state.mensagens.append({"role": "user", "parts": [prompt_usuario]})

    # 6.2 Chama a IA e exibe a resposta
    with container_chat:
        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                try:
                    # Monta a instrução de sistema injetando o currículo se disponível
                    contexto_curriculo = (
                        f"\n\n--- CURRÍCULO DE DENIS BOLFARINI ---\n{curriculo_texto}\n-------------------------------------"
                        if curriculo_texto.strip() else
                        "\n\n(Aviso: O usuário ainda não forneceu um currículo. Peça a ele para fazer o upload do PDF ou colar o currículo na barra lateral se ele pedir para adaptar seu perfil a alguma vaga)."
                    )
                    
                    # Instrução de Sistema (Persona do Agente)
                    config = types.GenerateContentConfig(
                        system_instruction=(
                            "Você é a Alia IA, uma Consultora de Carreira Sênior especialista em otimização de currículos e recolocação. "
                            "Seu objetivo é ajudar Denis Bolfarini a adaptar seu currículo (do LinkedIn ou PDF) para vagas de emprego específicas.\n\n"
                            "Diretrizes de Trabalho:\n"
                            "1. Quando Denis enviar a descrição de uma vaga, analise as palavras-chave, habilidades técnicas e competências mais valorizadas na vaga.\n"
                            "2. Compare esses requisitos com o currículo fornecido por Denis na barra lateral.\n"
                            "3. Se você notar que faltam informações importantes ou se precisar de detalhes sobre alguma experiência dele para valorizar no currículo para aquela vaga, faça UMA pergunta específica e estratégica antes de gerar a versão final.\n"
                            "4. Assim que tiver o contexto necessário, adapte o currículo. Melhore o resumo profissional, as atribuições nas experiências passadas e a lista de competências para enfatizar os pontos fortes compatíveis com a vaga, mantendo RIGOROSAMENTE a mesma estrutura original, ordem cronológica e estilo de formatação do currículo enviado.\n"
                            "5. SEMPRE apresente o currículo final adaptado completo dentro de um bloco de código Markdown (usando ```markdown ... ```) para que Denis consiga copiar o texto formatado inteiramente com apenas um clique no botão de cópia do Streamlit.\n"
                            "6. Destaque em negrito dentro do bloco de código as palavras-chave relevantes que foram inseridas para otimizar o currículo para filtros de IA (ATS).\n"
                            "7. Para garantir a formatação perfeita do cabeçalho no PDF gerado, inicie o bloco de código do currículo exatamente com:\n"
                            "   # Nome Completo\n"
                            "   ### Cargo Desejado\n"
                            "   Cidade - Estado | Telefone | E-mail | Link do LinkedIn | Link do GitHub (tudo na mesma linha, separado por ' | ')\n"
                            "8. Para cada Experiência Profissional e Formação Acadêmica, use obrigatoriamente a formatação H3 com o pipe separator para alinhar períodos à direita no PDF, exatamente assim:\n"
                            "   ### Nome da Empresa | Nome do Cargo | Período (Ex: Jan/2022 - Atual)\n"
                            "   ou\n"
                            "   ### Nome da Instituição | Nome do Curso | Período (Ex: 2018 - 2022)\n"
                            f"{contexto_curriculo}"
                        ),
                        temperature=0.7
                    )
                    
                    # Monta o histórico no formato exigido pela SDK do Gemini
                    historico_api = []
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

                    # Exibe a resposta no container do chat
                    st.markdown(texto_resposta)
                    
                    # Salva a resposta da IA no histórico local
                    st.session_state.mensagens.append({"role": "model", "parts": [texto_resposta]})
                    
                    # Força a atualização da página para carregar o novo currículo gerado no editor
                    st.rerun()
                    
                except Exception as err:
                    st.error(f"Ocorreu um erro ao comunicar com a IA: {err}")