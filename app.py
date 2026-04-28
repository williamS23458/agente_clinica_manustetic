"""
Aplicativo Streamlit para o Agente Manustetic
"""
import os
import re
import streamlit as st
from agent import agent, init_db, SERVICES, SERVICE_NAMES, now_saopaulo

init_db()

st.set_page_config(
    page_title="Manu Santos Esthetic - Assistente Virtual",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --sage-primary: #8B9D77;
        --sage-light: #D4DCC2;
        --sage-bg: #F5F5F0;
        --white: #FFFFFF;
    }
    .stApp { background-color: var(--sage-bg); }
    h1 { color: #5A6B4A !important; font-weight: 600 !important; }
    h2, h3 { color: var(--sage-primary) !important; }
    .logo-text { color: #5A6B4A; font-size: 1.8rem; font-weight: 700; text-align: center; margin-bottom: 0.5rem; }
    .logo-subtitle { color: var(--sage-primary); font-size: 0.9rem; text-align: center; margin-bottom: 1rem; font-style: italic; }
    .service-card { background: linear-gradient(135deg, var(--sage-light) 0%, var(--sage-bg) 100%); border-left: 4px solid var(--sage-primary); padding: 0.8rem; margin: 0.4rem 0; border-radius: 0 8px 8px 0; }
    .message-counter { font-size: 0.85rem; color: #888; text-align: center; padding: 0.5rem; margin-top: 1rem; border-top: 1px solid var(--sage-light); }
    .message-counter.warning { color: #C75B5B; font-weight: 600; }
    .limit-reached { background: linear-gradient(135deg, #F0E4E4 0%, #E8D6D6 100%); border: 2px solid #C75B5B; border-radius: 10px; padding: 1.5rem; text-align: center; margin: 2rem 0; }
    .stButton > button { background-color: var(--sage-primary) !important; color: white !important; border-radius: 25px !important; border: none !important; }
    .stButton > button:hover { background-color: #7A8D66 !important; }
    .whatsapp-button { background-color: #25D366 !important; color: white !important; padding: 0.8rem 1.5rem !important; border-radius: 25px !important; text-decoration: none !important; display: inline-block; font-weight: 600; }
    .stChatMessage { background-color: var(--white) !important; border-radius: 12px !important; }
    [data-testid="stSidebar"] { background-color: var(--white) !important; border-right: 1px solid var(--sage-light); }
    .info-box { background-color: var(--white); padding: 1rem; border-radius: 8px; border-left: 3px solid var(--sage-primary); margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)


def clean_response(text):
    """Remove function calls e JSON da resposta."""
    if not text:
        return text
    # Remove <function=...>...</function>
    text = re.sub(r'<function=.*?</function>', '', text, flags=re.DOTALL)
    # Remove {"name":...} JSON solto
    text = re.sub(r'\{"name".*?\}', '', text, flags=re.DOTALL)
    # Remove linhas vazias extras
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def get_response(prompt, context=""):
    """Obtém resposta do agente."""
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


# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "customer_name" not in st.session_state:
    st.session_state.customer_name = None
if "first_interaction" not in st.session_state:
    st.session_state.first_interaction = True
if "message_count" not in st.session_state:
    st.session_state.message_count = 0

MAX_MESSAGES = 30

# Sidebar
with st.sidebar:
    st.markdown("<div class='logo-text'>🌿 Manu Santos Esthetic</div>", unsafe_allow_html=True)
    st.markdown("<div class='logo-subtitle'>Estética & Bem-estar</div>", unsafe_allow_html=True)

    clinic_img = os.path.join(os.path.dirname(__file__), "clinica.jpg")
    if os.path.exists(clinic_img):
        st.image(clinic_img, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🕐 Horário de Funcionamento")
    st.markdown("**Segunda a Sábado** - 08:00 às 19:00")
    st.markdown("*Fechado aos domingos*")
    st.markdown("---")

    st.markdown("### ✨ Nossos Tratamentos")
    for service_name, service_info in SERVICES.items():
        with st.expander(f"**{service_name}** - {service_info['price']}"):
            st.markdown(f"<div class='info-box'>{service_info['description']}</div>", unsafe_allow_html=True)
            st.markdown(f"⏱️ Duração: **{service_info['duration']} minutos**")

    st.markdown("---")
    st.markdown("### 📞 Contato")
    st.markdown(
        "<a href='https://wa.me/5511951863253' target='_blank' class='whatsapp-button'>💬 WhatsApp</a>",
        unsafe_allow_html=True
    )
    st.markdown("<p style='text-align: center; margin-top: 0.5rem; font-size: 0.85rem; color: #666;'>+55 11 95186-3253</p>", unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state.customer_name:
        st.markdown(f"<p style='text-align: center; color: var(--sage-primary); font-weight: 500;'>👤 Olá, <strong>{st.session_state.customer_name}</strong>!</p>", unsafe_allow_html=True)

    counter_class = "warning" if st.session_state.message_count >= MAX_MESSAGES * 0.8 else ""
    st.markdown(f"<div class='message-counter {counter_class}'>💬 {st.session_state.message_count}/{MAX_MESSAGES} mensagens</div>", unsafe_allow_html=True)

    if st.button("🔄 Novo Chat"):
        st.session_state.messages = []
        st.session_state.customer_name = None
        st.session_state.first_interaction = True
        st.session_state.message_count = 0
        st.rerun()


# Área principal
st.title("Assistente Manustetic")
st.markdown("<p style='color: #666; font-size: 1.1rem; margin-bottom: 2rem;'>Agende sua visita com exclusividade</p>", unsafe_allow_html=True)

# Mensagem inicial
if st.session_state.first_interaction and len(st.session_state.messages) == 0:
    welcome = "Olá! Bem-vinda à Manu Santos Esthetic 🌿\n\nSou sua assistente virtual e estou aqui para ajudá-la a agendar seu tratamento estético.\n\nComo posso chamá-la?"
    st.session_state.messages.append({"role": "assistant", "content": welcome})
    st.session_state.first_interaction = False

# Exibe mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat
if st.session_state.message_count >= MAX_MESSAGES:
    st.markdown("""
    <div class='limit-reached'>
        <h3>🌿 Agradecemos sua visita!</h3>
        <p>Limite de mensagens atingido.</p>
        <p>Clique em "Novo Chat" para continuar.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    if prompt := st.chat_input("Digite sua mensagem..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.message_count += 1

        with st.chat_message("user"):
            st.markdown(prompt)

        # Extrai nome nas primeiras mensagens
        if st.session_state.customer_name is None and len(st.session_state.messages) <= 3:
            words = prompt.strip().split()
            if len(words) <= 3:
                st.session_state.customer_name = prompt.strip()

        with st.chat_message("assistant"):
            with st.spinner("Consultando agenda..."):
                context_parts = []
                if st.session_state.customer_name:
                    context_parts.append(f"Nome da cliente: {st.session_state.customer_name}")
                if len(st.session_state.messages) > 2:
                    recent = st.session_state.messages[-3:-1]
                    for msg in recent:
                        role = "Cliente" if msg["role"] == "user" else "Assistente"
                        context_parts.append(f"{role}: {msg['content'][:100]}")
                context = "\n".join(context_parts)

                response_content = get_response(prompt, context)

                if response_content is None:
                    response_content = "Desculpe, estou com dificuldades técnicas. 🌿\n\nEntre em contato pelo WhatsApp:\n📱 **+55 11 95186-3253**\n\nOu clique em 'Novo Chat' para reiniciar."

                st.markdown(response_content)

        st.session_state.messages.append({"role": "assistant", "content": response_content})

        if st.session_state.message_count >= MAX_MESSAGES:
            st.rerun()
