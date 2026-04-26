"""
Aplicativo Streamlit para o Agente Manustetic
"""
import streamlit as st
from agent import agent, init_db, SERVICES

init_db()

st.set_page_config(
    page_title="Manustetic - Assistente Virtual",
    page_icon="💆",
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
    h1 { color: #E91E8C !important; font-weight: 600 !important; }
    h2, h3 { color: #FF69B4 !important; }
    .logo-text {
        color: #E91E8C;
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }
    .service-card {
        background: linear-gradient(135deg, #FFF0F5 0%, #FFE4EC 100%);
        border-left: 4px solid #FF69B4;
        padding: 0.8rem;
        margin: 0.4rem 0;
        border-radius: 0 8px 8px 0;
    }
    .message-counter {
        font-size: 0.85rem;
        color: #888;
        text-align: center;
        padding: 0.5rem;
        margin-top: 1rem;
        border-top: 1px solid #FFB6C1;
    }
    .message-counter.warning { color: #FF6B6B; font-weight: 600; }
    .limit-reached {
        background: linear-gradient(135deg, #FFE4E4 0%, #FFD6D6 100%);
        border: 2px solid #FF6B6B;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        margin: 2rem 0;
    }
    .stButton > button {
        background-color: #FF69B4 !important;
        color: white !important;
        border-radius: 25px !important;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div class='logo-text'>💆 Manustetic</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🕐 Horário de Funcionamento")
    st.markdown("**Segunda a Sábado** - 08:00 às 19:00")
    st.markdown("*Fechado aos domingos*")
    st.markdown("---")
    st.markdown("### ✨ Nossos Serviços")
    for service in SERVICES:
        st.markdown(f"<div class='service-card'>✦ {service}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📞 Contato")
    st.markdown("Agende sua visita com exclusividade")
    message_count = len(st.session_state.get("messages", []))
    limit = 15
    counter_class = "warning" if message_count >= limit * 0.8 else ""
    st.markdown(f"<div class='message-counter {counter_class}'>💬 {message_count}/{limit} mensagens</div>", unsafe_allow_html=True)

st.title("Assistente Manustetic")
st.markdown("<p style='color: #888; font-size: 1.1rem;'>Agende sua visita com exclusividade</p>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_message = "Olá! Bem-vinda à Manustetic 💕 Sou sua assistente virtual e estou aqui para ajudá-la a agendar seu tratamento estético. Como posso ajudá-la hoje?"
    st.session_state.messages.append({"role": "assistant", "content": welcome_message})

message_count = len([m for m in st.session_state.messages if m["role"] == "user"])
MAX_MESSAGES = 15

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if message_count >= MAX_MESSAGES:
    st.markdown("<div class='limit-reached'><h3>💝 Agradecemos sua visita!</h3><p>Limite de mensagens atingido. Recarregue a página para continuar.</p></div>", unsafe_allow_html=True)
else:
    if prompt := st.chat_input("Digite sua mensagem..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Consultando agenda..."):
                chat_history = []
                for msg in st.session_state.messages[:-1]:
                    chat_history.append({"role": msg["role"], "content": msg["content"]})
                response = agent.run(
                    f"Histórico da conversa:\n{chat_history}\n\nNova mensagem do cliente: {prompt}"
                )
                if hasattr(response, 'content'):
                    response_content = response.content
                elif hasattr(response, 'messages') and response.messages:
                    response_content = response.messages[-1].content
                else:
                    response_content = str(response)
                st.markdown(response_content)
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        if len([m for m in st.session_state.messages if m["role"] == "user"]) >= MAX_MESSAGES:
            st.rerun()
