"""
Aplicativo Streamlit para o Agente Manustetic
"""
import os
import sys

# Configurar variáveis de ambiente a partir do st.secrets (Streamlit Cloud) antes de importar o agent
import streamlit as st

# Tenta carregar secrets do Streamlit Cloud
if hasattr(st, 'secrets'):
    for key in ['OPENAI_API_KEY', 'GOOGLE_CALENDAR_ID']:
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = st.secrets[key]

import re
import uuid
from agent import create_agent, init_db, SERVICES, SERVICE_NAMES, now_saopaulo

init_db()

st.set_page_config(
    page_title="Manu Santos Estetic - Assistente Virtual",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --bg-primary: #3A4232;
        --bg-card: #4A5240;
        --accent-primary: #7A9B6B;
        --accent-hover: #5E7A52;
        --text-primary: #F5F0E8;
        --text-highlight: #D4C9A8;
        --badge-confirmado: #7A9B6B;
        --badge-pendente: #D4C9A8;
        --badge-cancelado: #9B6B6B;
    }

    /* Fundo geral */
    .stApp {
        background: linear-gradient(135deg, #3A4232 0%, #2F3628 100%) !important;
    }

    /* Header degradê */
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #3A4232 0%, #4A5240 50%, #3A4232 100%) !important;
    }

    /* Títulos com ícones/cores */
    h1 {
        color: #D4C9A8 !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    h2 {
        color: #7A9B6B !important;
        border-bottom: 2px solid #7A9B6B;
        padding-bottom: 0.3rem;
    }
    h3 {
        color: #D4C9A8 !important;
    }

    /* Logo e textos */
    .logo-text {
        color: #D4C9A8;
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
    }
    .logo-subtitle {
        color: #7A9B6B;
        font-size: 0.9rem;
        text-align: center;
        margin-bottom: 1rem;
        font-style: italic;
    }

    /* Cards com borda colorida */
    .info-box {
        background: linear-gradient(135deg, #4A5240 0%, #525A46 100%);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #7A9B6B;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    /* Badges de status */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 0.5rem;
    }
    .badge-online { background-color: #7A9B6B; color: #F5F0E8; }
    .badge-exclusivo { background-color: #D4C9A8; color: #3A4232; }
    .badge-premium { background-color: #9B8B6B; color: #F5F0E8; }

    /* Separadores decorativos */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #7A9B6B 50%, transparent 100%);
        margin: 1.5rem 0;
        border: none;
    }

    /* Botões */
    .stButton > button {
        background: linear-gradient(135deg, #7A9B6B 0%, #6B8A5C 100%) !important;
        color: #F5F0E8 !important;
        border-radius: 25px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5E7A52 0%, #4A6342 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
    }

    /* Botão de tratamentos especial */
    .treatments-btn {
        background: linear-gradient(135deg, #D4C9A8 0%, #B8AD90 100%) !important;
        color: #3A4232 !important;
        font-weight: 700 !important;
        padding: 0.8rem 2rem !important;
        border-radius: 30px !important;
        border: 2px solid #F5F0E8 !important;
        box-shadow: 0 4px 15px rgba(212,201,168,0.3) !important;
        transition: all 0.3s ease !important;
    }
    .treatments-btn:hover {
        background: linear-gradient(135deg, #B8AD90 0%, #9C9174 100%) !important;
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(212,201,168,0.5) !important;
    }

    /* Botão WhatsApp */
    .whatsapp-button {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%) !important;
        color: #F5F0E8 !important;
        padding: 1rem 2rem !important;
        border-radius: 30px !important;
        text-decoration: none !important;
        display: inline-block;
        font-weight: 700;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(37,211,102,0.4) !important;
        transition: all 0.3s ease !important;
        border: 2px solid #F5F0E8 !important;
        animation: pulse 2s infinite;
    }
    .whatsapp-button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 25px rgba(37,211,102,0.6) !important;
    }
    @keyframes pulse {
        0% { box-shadow: 0 4px 15px rgba(37,211,102,0.4); }
        50% { box-shadow: 0 4px 25px rgba(37,211,102,0.7); }
        100% { box-shadow: 0 4px 15px rgba(37,211,102,0.4); }
    }

    /* Mensagens do chat */
    .stChatMessage {
        background: linear-gradient(135deg, #4A5240 0%, #525A46 100%) !important;
        border-radius: 15px !important;
        border: 1px solid #5A6B4A !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4A5240 0%, #3A4232 100%) !important;
        border-right: 2px solid #7A9B6B !important;
    }

    /* Counter de mensagens */
    .message-counter {
        font-size: 0.85rem;
        color: #D4C9A8;
        text-align: center;
        padding: 0.5rem;
        margin-top: 1rem;
        border-top: 1px solid #5A6B4A;
        background: rgba(122,155,107,0.1);
        border-radius: 8px;
    }
    .message-counter.warning {
        color: #E8C4C4;
        font-weight: 600;
        background: rgba(155,107,107,0.3);
    }

    /* Limite atingido card */
    .limit-reached {
        background: linear-gradient(135deg, #3A4232 0%, #4A5240 100%);
        border: 2px solid #D4C9A8;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .limit-reached h3 {
        color: #D4C9A8 !important;
        margin-bottom: 1rem;
    }

    /* Input do chat */
    .stChatInput {
        background: #4A5240 !important;
        border: 2px solid #5A6B4A !important;
        border-radius: 25px !important;
        color: #F5F0E8 !important;
    }

    /* Expander personalizado */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #5A6B4A 0%, #4A5A3A 100%) !important;
        border-radius: 10px !important;
        color: #F5F0E8 !important;
        font-weight: 600 !important;
        border: 1px solid #7A9B6B !important;
    }
    .streamlit-expanderContent {
        background: #4A5240 !important;
        border: 1px solid #5A6B4A !important;
        border-radius: 0 0 10px 10px !important;
        color: #F5F0E8 !important;
    }

    /* Textos gerais */
    p, span, div {
        color: #F5F0E8;
    }

    /* Indicador de ajuda human */
    .human-help-box {
        background: linear-gradient(135deg, #5A4A3A 0%, #6B5A4A 100%);
        border: 2px solid #D4C9A8;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(212,201,168,0.2);
    }
    .human-help-box p {
        color: #D4C9A8 !important;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)


def clean_response(text):
    if not text:
        return text
    text = re.sub(r'<function=.*?</function>', '', text, flags=re.DOTALL)
    text = re.sub(r'\{"name".*?\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def needs_human_help(response_text):
    """Verifica se a resposta indica que o agente não conseguiu atender"""
    if not response_text:
        return False

    phrases = [
        "não consigo",
        "não entendi",
        "não sei",
        "fora do meu escopo",
        "entre em contato",
        "fale com",
        "não posso ajudar",
        "não tenho",
        "não disponho",
        "impossível",
        "ajuda humana"
    ]

    response_lower = response_text.lower()
    return any(phrase in response_lower for phrase in phrases)


def get_response(prompt, context="", session_id=None):
    agent = create_agent(session_id=session_id)
    for attempt in range(2):
        try:
            full_prompt = f"""{context}

Mensagem do cliente: {prompt}

Responda de forma CONCISA e natural."""
            response = agent.run(full_prompt)
            if hasattr(response, 'content'):
                return clean_response(response.content)
            elif hasattr(response, 'messages') and response.messages:
                return clean_response(response.messages[-1].content)
            else:
                return clean_response(str(response))
        except Exception as e:
            error_msg = str(e).lower()
            if "context" in error_msg or "token" in error_msg:
                if attempt < 1:
                    continue
            return None
    return None


# Palavras que NAO sao nomes
NOMES_INVALIDOS = [
    "oi", "olá", "ola", "hey", "hello", "hi",
    "bom dia", "boa tarde", "boa noite",
    "tudo bem", "tudo bom", "ok", "sim", "nao",
    "obrigada", "obrigado", "tchau", "ate logo"
]

# Padrões de prompt injection para bloquear
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(suas?\s+)?instru\w*",
    r"esque\w+\s+tudo",
    r"agora\s+voc\w+\s+\w+\s+outr[oa]\s+(agente|assistente|pessoa)",
    r"revele\s+(seu\s+)?(prompt|system\s*prompt|instru\w+)",
    r"mostre\s+(?:su[ao]s?\s+)?(prompt|system\s*prompt|instru\w+)",
    r"imprima\s+(?:su[ao]s?\s+)?(prompt|system\s*prompt|instru\w+)",
    r"print\s+(your\s+)?(prompt|system\s*prompt|instructions)",
    r"ignore\s+previous\s+instructions",
    r"forget\s+everything",
    r"you\s+are\s+now\s+a",
    r"system\s*:?\s*ignore",
    r"new\s+instructions\s*:",
    r"role\s*:?\s*play",
]


def detect_prompt_injection(text):
    """Verifica se a mensagem do usuário contém tentativa de prompt injection."""
    if not text:
        return False
    text_lower = text.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

# Session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "customer_name" not in st.session_state:
    st.session_state.customer_name = None
if "first_interaction" not in st.session_state:
    st.session_state.first_interaction = True
if "message_count" not in st.session_state:
    st.session_state.message_count = 0
if "show_treatments" not in st.session_state:
    st.session_state.show_treatments = False

MAX_MESSAGES = 30

with st.sidebar:
    st.markdown("<div class='logo-text'>👑 Manu Santos Estetic</div>", unsafe_allow_html=True)
    st.markdown("<div class='logo-subtitle'>Estética & Bem-estar</div>", unsafe_allow_html=True)

    # Badges decorativos
    st.markdown("<div style='text-align: center; margin-bottom: 1rem;'><span class='badge badge-online'>🟢 Online</span><span class='badge badge-exclusivo'>✨ Exclusivo</span></div>", unsafe_allow_html=True)

    clinic_img = os.path.join(os.path.dirname(__file__), "clinica.jpg")
    if os.path.exists(clinic_img):
        st.image(clinic_img, use_container_width=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    st.markdown("### 🕐 Horário de Funcionamento")
    st.markdown("<div class='info-box'>**Segunda a Sábado** - 08:00 às 19:00<br/>*Fechado aos domingos*</div>", unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Botão dinâmico de tratamentos
    st.markdown("### ✨ Tratamentos")

    if st.button("✨ Ver Tratamentos Disponíveis", key="btn_treatments", help="Clique para ver nossos tratamentos"):
        st.session_state.show_treatments = not st.session_state.show_treatments

    if st.session_state.show_treatments:
        with st.expander("Tratamentos Disponíveis", expanded=True):
            for service_name, service_info in SERVICES.items():
                st.markdown(f"""
                <div style='background: rgba(90,107,74,0.3); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 3px solid #7A9B6B;'>
                    <strong style='color: #D4C9A8; font-size: 1.1rem;'>💫 {service_name}</strong><br/>
                    <span style='color: #F5F0E8; font-size: 0.9rem;'>{service_info['description']}</span><br/>
                    <span style='color: #7A9B6B; font-size: 0.85rem;'>⏱️ Duração: {service_info['duration']} minutos</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    st.markdown("### 📞 Contato")
    st.markdown("<a href='https://wa.me/5511951863253' target='_blank' class='whatsapp-button'>💬 Falar no WhatsApp</a>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: 0.5rem; font-size: 0.85rem; color: #D4C9A8;'>+55 11 95186-3253</p>", unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    if st.session_state.customer_name:
        st.markdown(f"<p style='text-align: center; color: #7A9B6B; font-weight: 600; font-size: 1.1rem;'>👤 Olá, <strong>{st.session_state.customer_name}</strong>!</p>", unsafe_allow_html=True)

    counter_class = "warning" if st.session_state.message_count >= MAX_MESSAGES * 0.8 else ""
    st.markdown(f"<div class='message-counter {counter_class}'>💬 {st.session_state.message_count}/{MAX_MESSAGES} mensagens</div>", unsafe_allow_html=True)

    if st.button("🔄 Novo Chat"):
        st.session_state.messages = []
        st.session_state.customer_name = None
        st.session_state.first_interaction = True
        st.session_state.message_count = 0
        st.session_state.show_treatments = False
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()


st.markdown("""
<style>
    .lgpd-banner {
        background: #2C3E2C;
        border: 1px solid #7A9B6B;
        border-radius: 10px;
        padding: 0.75rem;
        margin-bottom: 1rem;
        text-align: center;
        font-size: 0.85rem;
        color: #D4C9A8;
    }
</style>
<div class='lgpd-banner'>
    🔒 <strong>Privacidade garantida</strong> — Seus dados são opcionais e usados apenas para lembretes e promoções, conforme a <em>LGPD</em>.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='background: linear-gradient(90deg, #3A4232 0%, #4A5240 30%, #5A6B4A 50%, #4A5240 70%, #3A4232 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3);'>
    <h1 style='margin: 0; color: #D4C9A8 !important; font-size: 2rem;'>👑 Assistente Manustetic</h1>
    <p style='color: #F5F0E8; margin: 0.5rem 0 0 0; font-size: 1.1rem;'>Agende sua visita com exclusividade</p>
</div>
""", unsafe_allow_html=True)

# Banner Especial Dia das Mães
st.markdown("""
<style>
    .mothers-day-banner {
        background: linear-gradient(135deg, #FFE4E1 0%, #FFDAB9 50%, #FFF8DC 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(212, 175, 55, 0.3);
        border: 2px solid #DAA520;
    }
    .mothers-day-title {
        text-align: center;
        color: #8B4513 !important;
        font-size: 1.8rem !important;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .mothers-day-cards {
        display: flex;
        gap: 1rem;
        justify-content: center;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    }
    .mothers-day-card {
        background: linear-gradient(135deg, #FFF 0%, #FFF5EE 100%);
        border-radius: 12px;
        padding: 1rem;
        width: 280px;
        border: 2px solid #DDA0DD;
        box-shadow: 0 3px 10px rgba(0,0,0,0.15);
        transition: transform 0.3s ease;
    }
    .mothers-day-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
    .mothers-day-card h4 {
        color: #8B008B !important;
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem !important;
    }
    .mothers-day-card .old-price {
        text-decoration: line-through;
        color: #999;
        font-size: 0.9rem;
    }
    .mothers-day-card .new-price {
        color: #228B22;
        font-size: 1.4rem;
        font-weight: bold;
    }
    .mothers-day-card .includes {
        color: #555;
        font-size: 0.85rem;
        margin-top: 0.5rem;
        line-height: 1.4;
    }
    .mothers-day-footer {
        text-align: center;
        color: #8B4513;
        font-weight: 600;
        font-size: 0.95rem;
        margin-top: 0.5rem;
    }
    .mothers-day-btn {
        display: inline-block;
        background: linear-gradient(135deg, #DDA0DD 0%, #DA70D6 100%) !important;
        color: #FFF !important;
        padding: 0.8rem 2rem !important;
        border-radius: 25px !important;
        text-decoration: none !important;
        font-weight: bold !important;
        border: 2px solid #8B008B !important;
        box-shadow: 0 4px 15px rgba(218, 112, 214, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .mothers-day-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(218, 112, 214, 0.6) !important;
    }
</style>

<div class="mothers-day-banner">
    <h2 class="mothers-day-title">🌸💐 Especial Dia das Mães 💐🌸</h2>
    <div class="mothers-day-cards">
        <div class="mothers-day-card">
            <h4>✨ Protocolo Cuide-se Bem</h4>
            <span class="old-price">De R$180</span>
            <span class="new-price"> por R$149</span>
            <div class="includes">
                🌷 Design de sobrancelhas<br>
                🌷 Nutrigloss<br>
                🌷 Hidratação facial<br>
                🌷 Massagem facial
            </div>
        </div>
        <div class="mothers-day-card">
            <h4>✨ Protocolo Momento Relax</h4>
            <span class="old-price">De R$240</span>
            <span class="new-price"> por R$199</span>
            <div class="includes">
                🌷 Limpeza de pele<br>
                🌷 Hidragloss<br>
                🌷 Drenagem facial<br>
                🌷 Massagem craniana<br>
                🌷 Massagem nos pés
            </div>
        </div>
        <div class="mothers-day-card">
            <h4>👑 Protocolo Dia de Rainha</h4>
            <span class="old-price">De R$280</span>
            <span class="new-price"> por R$235</span>
            <div class="includes">
                🌷 Massagem relaxante<br>
                🌷 Hidratação facial<br>
                🌷 Nutrigloss<br>
                🌷 Massagem facial<br>
                🌷 Massagem nos pés<br>
                🌷 Massagem craniana
            </div>
        </div>
    </div>
    <div style="text-align: center; margin: 1rem 0;">
        <p class="mothers-day-footer">⏰ Válido até 11/05 - Agende pelo chat!</p>
    </div>
    <div style="text-align: center;">
        <a href="https://wa.me/5511951863253" target="_blank" class="mothers-day-btn">Quero agendar meu protocolo! 💖</a>
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.first_interaction and len(st.session_state.messages) == 0:
    welcome = "Olá! Bem-vinda à Manu Santos Estetic 👑\n\nSou sua assistente virtual e estou aqui para ajudá-la a agendar seu tratamento estético.\n\nComo posso chamá-la?"
    st.session_state.messages.append({"role": "assistant", "content": welcome})
    st.session_state.first_interaction = False

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Verifica se mensagem do assistente precisa de ajuda humana
        if message["role"] == "assistant" and needs_human_help(message["content"]):
            st.markdown("""
            <div class='human-help-box'>
                <p>👑 Gostaria de falar diretamente com a esteticista?</p>
                <a href='https://wa.me/5511951863253' target='_blank' class='whatsapp-button'>💬 Falar com a Esteticista no WhatsApp</a>
            </div>
            """, unsafe_allow_html=True)

if st.session_state.message_count >= MAX_MESSAGES:
    st.markdown("""
    <div class='limit-reached'>
        <h3>👑 Agradecemos sua visita!</h3>
        <p>Limite de mensagens atingido.</p>
        <p>Clique em "Novo Chat" para continuar.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Verifica tentativa de prompt injection
        if detect_prompt_injection(prompt):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.message_count += 1
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                response_content = "Desculpe, não posso ajudar com isso. Estou aqui para falar sobre nossos tratamentos estéticos e agendamentos. Como posso ajudá-la hoje? 🌿"
                st.markdown(response_content)
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.message_count += 1

        with st.chat_message("user"):
            st.markdown(prompt)

        # Captura nome filtrando palavras invalidas
        if st.session_state.customer_name is None and len(st.session_state.messages) <= 4:
            words = prompt.strip().split()
            if 1 <= len(words) <= 3 and prompt.strip().lower() not in NOMES_INVALIDOS:
                st.session_state.customer_name = prompt.strip()

        with st.chat_message("assistant"):
            with st.spinner("Consultando agenda..."):
                context_parts = []
                if st.session_state.customer_name:
                    context_parts.append(f"Nome da cliente: {st.session_state.customer_name}")
                for msg in st.session_state.messages[:-1]:
                    role = "Cliente" if msg["role"] == "user" else "Assistente"
                    context_parts.append(f"{role}: {msg['content']}")
                context = "\n".join(context_parts)

                response_content = get_response(
                    prompt,
                    context,
                    session_id=st.session_state.session_id
                )

                if response_content is None:
                    response_content = "Desculpe, estou com dificuldades técnicas. 🌿\n\nEntre em contato pelo WhatsApp:\n📱 **+55 11 95186-3253**\n\nOu clique em 'Novo Chat' para reiniciar."

                st.markdown(response_content)

                # Verifica se resposta precisa de ajuda humana
                if needs_human_help(response_content):
                    st.markdown("""
                    <div class='human-help-box'>
                        <p>🌿 Gostaria de falar diretamente com a esteticista?</p>
                        <a href='https://wa.me/5511951863253' target='_blank' class='whatsapp-button'>💬 Falar com a Esteticista no WhatsApp</a>
                    </div>
                    """, unsafe_allow_html=True)

        st.session_state.messages.append({"role": "assistant", "content": response_content})

        if st.session_state.message_count >= MAX_MESSAGES:
            st.rerun()
