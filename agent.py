"""Agente Manustetic - Versão Estável e Robusta"""
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.toolkit import Toolkit
from agno.tools import tool

load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('manustetic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SAO_PAULO_TZ = ZoneInfo('America/Sao_Paulo')


def now_saopaulo():
    return datetime.now(SAO_PAULO_TZ)


SERVICES = {
    "Limpeza de Pele": {"price": "R$ 140,00", "duration": 60, "description": "Tratamento profundo que remove impurezas, cravos e células mortas."},
    "Microagulhamento Facial": {"price": "R$ 150,00", "duration": 45, "description": "Estimula colágeno e elastina."},
    "Microagulhamento Estrias": {"price": "Avaliar", "duration": 60, "description": "Estimula regeneração da pele em estrias."},
    "Dermaplening": {"price": "R$ 50,00", "duration": 30, "description": "Esfoliação profunda."},
    "Nutri Gloss": {"price": "R$ 100,00", "duration": 45, "description": "Hidratação intensa com brilho saudável."},
    "Design de Sobrancelhas": {"price": "R$ 30,00", "duration": 30, "description": "Modelagem profissional."},
    "Massagem Relaxante": {"price": "R$ 120,00", "duration": 60, "description": "Alivia tensões musculares."},
    "Drenagem Corporal": {"price": "R$ 120,00", "duration": 60, "description": "Estimula sistema linfático."},
    "Massagem Miofacial": {"price": "R$ 130,00", "duration": 60, "description": "Massagem profunda."},
    "Epilação a Laser": {"price": "Avaliar", "duration": 60, "description": "Remoção definitiva de pelos."}
}

SERVICE_NAMES = list(SERVICES.keys())
DB_PATH = "appointments.db"


def init_db():
    """Inicializa o banco de dados com a estrutura correta."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Cria tabela appointments com os nomes de colunas corretos
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            service TEXT,
            appointment_date TEXT,
            appointment_time TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Cria tabela customers
    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT,
            birthday TEXT,
            accept_marketing BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_visit TIMESTAMP,
            total_appointments INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Banco de dados inicializado")


def parse_natural_date(date_str):
    """Converte data natural para formato ISO (YYYY-MM-DD)."""
    if not date_str:
        return None

    s = str(date_str).lower().strip()
    today = now_saopaulo().date()

    # Datas naturais
    if s in ["hoje", "hj"]:
        return today.isoformat()
    if s in ["amanha", "amanhã"]:
        return (today + timedelta(days=1)).isoformat()
    if s in ["depois de amanha", "depois de amanhã"]:
        return (today + timedelta(days=2)).isoformat()

    # Formatos de data
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m", "%d-%m"]
    for fmt in formats:
        try:
            p = datetime.strptime(s, fmt)
            if fmt in ["%d/%m", "%d-%m"]:
                p = p.replace(year=today.year)
                if p.date() < today:
                    p = p.replace(year=today.year + 1)
            return p.date().isoformat()
        except ValueError:
            continue

    return None


def check_time_conflict(date_str, time_str, duration=60):
    """Verifica se há conflito de horário."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Hora de início e fim do novo agendamento
        rs = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        re = rs + timedelta(minutes=duration)

        # Busca todos os agendamentos do dia
        c.execute("SELECT appointment_time, service FROM appointments WHERE appointment_date = ?", (date_str,))
        rows = c.fetchall()
        conn.close()

        for t, s in rows:
            es = datetime.strptime(f"{date_str} {t}", "%Y-%m-%d %H:%M")
            ee = es + timedelta(minutes=SERVICES.get(s, {}).get("duration", 60))

            # Verifica sobreposição
            if rs < ee and re > es:
                return True

        return False
    except Exception as e:
        logger.error(f"Erro ao verificar conflito: {e}")
        return False


class ManusteticTools(Toolkit):
    def __init__(self):
        super().__init__(name="manustetic_tools")
        self.register(self.add_appointment)
        self.register(self.list_appointments)
        self.register(self.get_available_slots)
        self.register(self.cancel_appointment)

    @tool
    def add_appointment(self, customer_name: str, service: str, date: str = None,
                       time: str = None, appointment_date: str = None,
                       appointment_time: str = None, phone: str = None) -> str:
        """
        Agenda um novo compromisso.

        Args:
            customer_name: Nome do cliente
            service: Nome do serviço
            date: Data do agendamento (pode ser natural: hoje, amanhã, 27/04)
            time: Horário do agendamento (formato HH:MM)
            appointment_date: Alias para date
            appointment_time: Alias para time
            phone: Telefone do cliente
        """
        try:
            # Usa date ou appointment_date
            fd = date or appointment_date
            ft = time or appointment_time

            if not fd or not ft:
                return "Preciso da data e do horário do agendamento."

            # Faz parse da data
            pd = parse_natural_date(fd)
            if not pd:
                return f"Data '{fd}' não reconhecida. Pode usar: hoje, amanhã, 27/04, etc."

            # Valida serviço
            if service not in SERVICE_NAMES:
                return f"Serviço '{service}' não encontrado. Disponíveis: {', '.join(SERVICE_NAMES)}"

            # Valida horário de funcionamento
            try:
                h = int(ft.split(":")[0])
                if h < 8 or h >= 19:
                    return "Horário fora do expediente. Funcionamos de Segunda a Sábado das 08:00 às 19:00."
            except:
                return f"Horário '{ft}' inválido. Use formato HH:MM (ex: 14:00)"

            # Verifica conflito
            duration = SERVICES[service]["duration"]
            if check_time_conflict(pd, ft, duration):
                return f"Já existe um agendamento para {ft}. Posso verificar outros horários disponíveis para você."

            # Insere no banco
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO appointments (customer_name, service, appointment_date, appointment_time, phone) VALUES (?, ?, ?, ?, ?)",
                (customer_name, service, pd, ft, phone)
            )
            conn.commit()
            conn.close()

            logger.info(f"Agendamento criado: {customer_name}, {service}, {pd} {ft}")
            return f"Agendamento confirmado! ✅\n\nCliente: {customer_name}\nServiço: {service}\nData: {pd}\nHorário: {ft}\n\nAguardamos você! 🌿"

        except Exception as e:
            logger.error(f"Erro ao criar agendamento: {e}")
            return "Desculpe, ocorreu um erro ao criar o agendamento. Por favor, tente novamente ou entre em contato pelo WhatsApp."

    @tool
    def list_appointments(self, customer_name: str = None) -> str:
        """
        Lista agendamentos.

        Args:
            customer_name: Nome do cliente (opcional, se não informar lista todos)
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            today = now_saopaulo().date().isoformat()

            if customer_name:
                c.execute(
                    "SELECT * FROM appointments WHERE customer_name LIKE ? AND appointment_date >= ? ORDER BY appointment_date, appointment_time",
                    (f"%{customer_name}%", today)
                )
            else:
                c.execute(
                    "SELECT * FROM appointments WHERE appointment_date >= ? ORDER BY appointment_date, appointment_time",
                    (today,)
                )

            rows = c.fetchall()
            conn.close()

            if not rows:
                if customer_name:
                    return f"Nenhum agendamento encontrado para '{customer_name}'."
                return "Nenhum agendamento encontrado."

            r = "📅 Agendamentos futuros:\n\n"
            for a in rows:
                r += f"• {a[1]} - {a[2]} em {a[3]} às {a[4]}\n"
            return r

        except Exception as e:
            logger.error(f"Erro ao listar agendamentos: {e}")
            return "Desculpe, não consegui consultar os agendamentos. Por favor, tente novamente."

    @tool
    def get_available_slots(self, date: str = None, appointment_date: str = None) -> str:
        """
        Mostra horários disponíveis para uma data.

        Args:
            date: Data desejada (pode ser natural: hoje, amanhã, 27/04)
            appointment_date: Alias para date
        """
        try:
            fd = date or appointment_date
            if not fd:
                return "Por favor, informe uma data para eu verificar os horários disponíveis."

            pd = parse_natural_date(fd)
            if not pd:
                return f"Data '{fd}' não reconhecida. Pode usar: hoje, amanhã, 27/04, etc."

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT appointment_time FROM appointments WHERE appointment_date = ?", (pd,))
            booked = [r[0] for r in c.fetchall()]
            conn.close()

            # Horários de funcionamento: 08:00 às 19:00
            all_slots = [f"{h:02d}:00" for h in range(8, 19)]
            avail = [s for s in all_slots if s not in booked]

            if not avail:
                return f"Não há horários disponíveis para {pd}. Posso verificar outra data para você."

            return f"Horários disponíveis em {pd}:\n" + "\n".join([f"• {s}" for s in avail])

        except Exception as e:
            logger.error(f"Erro ao buscar horários: {e}")
            return "Desculpe, não consegui verificar os horários. Por favor, tente novamente."

    @tool
    def cancel_appointment(self, customer_name: str, date: str = None, appointment_date: str = None) -> str:
        """
        Cancela um agendamento.

        Args:
            customer_name: Nome do cliente
            date: Data do agendamento
            appointment_date: Alias para date
        """
        try:
            fd = date or appointment_date
            if not fd:
                return "Preciso da data do agendamento para cancelar."

            pd = parse_natural_date(fd) or fd

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "DELETE FROM appointments WHERE customer_name LIKE ? AND appointment_date = ?",
                (f"%{customer_name}%", pd)
            )
            conn.commit()
            deleted = c.rowcount
            conn.close()

            if deleted > 0:
                return f"Agendamento cancelado com sucesso! ✅"
            else:
                return f"Não encontrei agendamento para {customer_name} em {pd}."

        except Exception as e:
            logger.error(f"Erro ao cancelar agendamento: {e}")
            return "Desculpe, ocorreu um erro ao cancelar. Por favor, entre em contato pelo WhatsApp."


# Cria o agente com instruções claras e limites de contexto
system_prompt = f"""Você é a assistente virtual da Manu Santos Esthetic - uma clínica de estética e bem-estar.

PERSONALIDADE:
- Calorosa, acolhedora e profissional
- Use emojis sutilmente (🌿, ✨, 💚)
- Seja CONCISA nas respostas (máximo 3-4 parágrafos)
- Trate as clientes pelo nome quando souber

SERVIÇOS DISPONÍVEIS:
{chr(10).join([f"• {n}: {i['price']} ({i['duration']} min)" for n, i in SERVICES.items()])}

INFORMAÇÕES DA CLÍNICA:
- Horário: Segunda a Sábado, 08:00 às 19:00
- WhatsApp: +55 11 95186-3253
- Endereço: Consultório particular

REGRAS IMPORTANTES:
1. Pergunte o nome da cliente na PRIMEIRA interação
2. Sempre confirme os dados antes de agendar (nome, serviço, data, horário)
3. Use as ferramentas para verificar conflitos ANTES de confirmar
4. Se houver erro, NÃO mostre código de erro - apenas peça para tentar novamente
5. Limite-se a 3-4 interações por contexto - não acumule histórico excessivo
6. Se não souber algo, sugira o WhatsApp +55 11 95186-3253

DATA E HORA ATUAL: {now_saopaulo().strftime('%Y-%m-%d %H:%M')}
"""

agent = Agent(
    name="Manustetic",
    model=Groq(
        id="openai/gpt-oss-120b",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7,
        max_tokens=1024
    ),
    tools=[ManusteticTools()],
    description=system_prompt
)

init_db()
logger.info("Agente Manustetic inicializado com sucesso")
