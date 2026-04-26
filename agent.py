"""
Agente de Agendamento para Clínica Manustetic
Usando framework Agno com Groq
"""
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool
from dotenv import load_dotenv

load_dotenv()

# Configurações
DB_FILE = "appointments.db"
BUSINESS_HOURS_START = 8
BUSINESS_HOURS_END = 19
PROCEDURE_DURATION = 60  # minutos

SERVICES = [
    "Limpeza de Pele",
    "Botox",
    "Preenchimento Labial",
    "Drenagem Linfática",
    "Massagem Modeladora",
    "Design de Sobrancelhas"
]


def init_db():
    """Inicializa o banco de dados SQLite com a tabela appointments."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            appointment_time TIMESTAMP NOT NULL,
            service TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT (datetime('now'))
        )
    """)
    conn.close()


def get_db_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def generate_appointment_id() -> str:
    """Gera um ID único para o agendamento no formato APPT-{timestamp}."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"APPT-{timestamp}"


def parse_datetime(date_str: str) -> Optional[datetime]:
    """Converte string de data no formato dd-mm-yyyy HH:MM para datetime."""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y %H:%M")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%d-%m-%y %H:%M")
        except ValueError:
            return None


def format_datetime(dt: datetime) -> str:
    """Formata datetime para string no formato dd-mm-yyyy HH:MM."""
    return dt.strftime("%d-%m-%Y %H:%M")


def is_within_business_hours(dt: datetime) -> bool:
    """Verifica se o horário está dentro do horário de funcionamento."""
    if dt.weekday() == 6:  # Domingo
        return False
    hour = dt.hour
    return BUSINESS_HOURS_START <= hour < BUSINESS_HOURS_END


def get_free_slots(date_str: str) -> List[str]:
    """Retorna lista de horários livres para uma data específica."""
    dt = parse_datetime(f"{date_str} 00:00")
    if not dt:
        return []
    
    # Buscar todos os horários ocupados na data
    conn = get_db_connection()
    start_of_day = dt.replace(hour=0, minute=0, second=0)
    end_of_day = dt.replace(hour=23, minute=59, second=59)
    
    result = conn.execute("""
        SELECT appointment_time 
        FROM appointments 
        WHERE appointment_time >= ? 
        AND appointment_time <= ?
        AND status IN ('scheduled', 'rescheduled')
        ORDER BY appointment_time
    """, [start_of_day, end_of_day]).fetchall()
    
    occupied_slots = [row[0] for row in result]
    conn.close()
    
    # Gerar todos os horários possíveis
    all_slots = []
    current = dt.replace(hour=BUSINESS_HOURS_START, minute=0)
    end_time = dt.replace(hour=BUSINESS_HOURS_END, minute=0)
    
    while current < end_time:
        all_slots.append(current)
        current += timedelta(minutes=PROCEDURE_DURATION)
    
    # Filtrar horários ocupados
    free_slots = []
    for slot in all_slots:
        slot_occupied = False
        for occupied in occupied_slots:
            if abs((slot - occupied).total_seconds()) < PROCEDURE_DURATION * 60:
                slot_occupied = True
                break
        if not slot_occupied:
            free_slots.append(format_datetime(slot))
    
    return free_slots


def find_next_available_slots(from_time: datetime, count: int = 3) -> List[str]:
    """Encontra os próximos horários livres a partir de um horário."""
    slots = []
    current = from_time
    attempts = 0
    max_attempts = 30
    
    while len(slots) < count and attempts < max_attempts:
        if is_within_business_hours(current):
            date_str = current.strftime("%d-%m-%Y")
            free_slots = get_free_slots(date_str)
            
            for slot in free_slots:
                slot_dt = parse_datetime(slot)
                if slot_dt and slot_dt >= current:
                    slots.append(slot)
                    if len(slots) >= count:
                        break
        
        current += timedelta(hours=1)
        attempts += 1
    
    return slots[:count]


# ============================================
# TOOLS DO AGENTE
# ============================================

@tool
def schedule_appointment(customer_name: str, appointment_time: str, service: str) -> str:
    """
    Agenda um novo atendimento na clínica.
    
    Args:
        customer_name: Nome do cliente
        appointment_time: Data e hora no formato dd-mm-yyyy HH:MM
        service: Nome do serviço/procedimento
    
    Returns:
        Mensagem de confirmação ou sugestão de horários alternativos
    """
    # Validar formato da data
    dt = parse_datetime(appointment_time)
    if not dt:
        return f"Formato de data inválido. Use o formato: dd-mm-yyyy HH:MM (ex: 25-04-2026 14:00)"
    
    # Validar horário de funcionamento
    if not is_within_business_hours(dt):
        return "Desculpe! Nosso horário de funcionamento é de Segunda a Sábado, das 08:00 às 19:00."
    
    # Verificar se o serviço existe
    service_match = None
    for s in SERVICES:
        if service.lower() in s.lower() or s.lower() in service.lower():
            service_match = s
            break
    
    if not service_match:
        services_list = "\n".join([f"  • {s}" for s in SERVICES])
        return f"Serviço não encontrado. Nossos serviços são:\n{services_list}"
    
    # Verificar conflitos
    conn = get_db_connection()
    result = conn.execute("""
        SELECT id FROM appointments 
        WHERE appointment_time >= ? 
        AND appointment_time < ?
        AND status IN ('scheduled', 'rescheduled')
    """, [dt, dt + timedelta(minutes=PROCEDURE_DURATION)]).fetchone()
    conn.close()
    
    if result:
        # Horário ocupado - sugerir alternativas
        alternatives = find_next_available_slots(dt, 3)
        if alternatives:
            alt_text = "\n".join([f"  • {alt}" for alt in alternatives])
            return f"""Esse horário já está reservado. Posso oferecer as seguintes opções:
{alt_text}
Qual prefere, {customer_name}?"""
        else:
            return f"Esse horário já está reservado. Infelizmente não encontrei horários disponíveis próximos. Por favor, tente outra data."
    
    # Horário livre - criar agendamento
    appointment_id = generate_appointment_id()
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO appointments (id, customer_name, appointment_time, service, status)
        VALUES (?, ?, ?, ?, 'scheduled')
    """, [appointment_id, customer_name, dt, service_match])
    conn.commit()
    conn.close()
    
    return f"Agendamento confirmado! \nID: {appointment_id}\nCliente: {customer_name}\nServiço: {service_match}\nData/Horário: {appointment_time}"


@tool
def reschedule_appointment(appointment_id: str, new_time: str) -> str:
    """
    Remarca um agendamento existente.
    
    Args:
        appointment_id: ID do agendamento (formato APPT-...)
        new_time: Nova data e hora no formato dd-mm-yyyy HH:MM
    
    Returns:
        Mensagem de confirmação ou sugestão de horários alternativos
    """
    # Validar formato da data
    dt = parse_datetime(new_time)
    if not dt:
        return f"Formato de data inválido. Use o formato: dd-mm-yyyy HH:MM (ex: 25-04-2026 14:00)"
    
    # Validar horário de funcionamento
    if not is_within_business_hours(dt):
        return "Desculpe! Nosso horário de funcionamento é de Segunda a Sábado, das 08:00 às 19:00."
    
    # Verificar se o agendamento existe
    conn = get_db_connection()
    result = conn.execute("""
        SELECT customer_name FROM appointments 
        WHERE id = ?
    """, [appointment_id]).fetchone()
    
    if not result:
        conn.close()
        return "Agendamento não encontrado. Verifique o ID e tente novamente."
    
    customer_name = result[0]
    
    # Verificar se o novo horário está livre
    conflict = conn.execute("""
        SELECT id FROM appointments 
        WHERE appointment_time >= ? 
        AND appointment_time < ?
        AND status IN ('scheduled', 'rescheduled')
        AND id != ?
    """, [dt, dt + timedelta(minutes=PROCEDURE_DURATION), appointment_id]).fetchone()
    conn.close()
    
    if conflict:
        # Horário ocupado - sugerir alternativas
        alternatives = find_next_available_slots(dt, 3)
        if alternatives:
            alt_text = "\n".join([f"  • {alt}" for alt in alternatives])
            return f"""O horário {new_time} já está reservado. Posso oferecer:
{alt_text}
Qual prefere?"""
        else:
            return f"O horário {new_time} já está reservado. Infelizmente não encontrei horários disponíveis próximos."
    
    # Horário livre - atualizar agendamento
    conn = get_db_connection()
    conn.execute("""
        UPDATE appointments 
        SET appointment_time = ?, status = 'rescheduled'
        WHERE id = ?
    """, [dt, appointment_id])
    conn.commit()
    conn.close()
    
    return f"Agendamento remarcado com sucesso!\nID: {appointment_id}\nNovo horário: {new_time}"


@tool
def cancel_appointment(appointment_id: str) -> str:
    """
    Cancela um agendamento existente.
    
    Args:
        appointment_id: ID do agendamento (formato APPT-...)
    
    Returns:
        Mensagem de confirmação
    """
    conn = get_db_connection()
    result = conn.execute("""
        SELECT customer_name, appointment_time, service 
        FROM appointments 
        WHERE id = ?
    """, [appointment_id]).fetchone()
    
    if not result:
        conn.close()
        return "Agendamento não encontrado. Verifique o ID e tente novamente."
    
    customer_name, appointment_time, service = result
    
    conn.execute("""
        UPDATE appointments 
        SET status = 'cancelled' 
        WHERE id = ?
    """, [appointment_id])
    conn.commit()
    conn.close()
    
    return f"Agendamento cancelado com sucesso!\nID: {appointment_id}\nCliente: {customer_name}\nServiço: {service}\nHorário: {format_datetime(appointment_time)}"


@tool
def get_upcoming_appointments(customer_name: str) -> str:
    """
    Busca os próximos agendamentos de um cliente.
    
    Args:
        customer_name: Nome do cliente
    
    Returns:
        Lista formatada dos agendamentos futuros
    """
    conn = get_db_connection()
    result = conn.execute("""
        SELECT id, appointment_time, service, status
        FROM appointments 
        WHERE LOWER(customer_name) LIKE LOWER(?)
        AND appointment_time > datetime('now')
        AND status IN ('scheduled', 'rescheduled')
        ORDER BY appointment_time
    """, [f"%{customer_name}%"]).fetchall()
    conn.close()
    
    if not result:
        return f"Não encontrei agendamentos futuros para {customer_name}."
    
    appointments_list = []
    for row in result:
        appointment_id, apt_time, service, status = row
        status_pt = "Confirmado" if status == "scheduled" else "Remarcado"
        appointments_list.append(f"  • {format_datetime(apt_time)} - {service} (ID: {appointment_id}) - {status_pt}")
    
    return f"Próximos agendamentos de {customer_name}:\n" + "\n".join(appointments_list)


@tool
def suggest_free_slots(date: str) -> str:
    """
    Sugere horários disponíveis para uma data específica.
    
    Args:
        date: Data no formato dd-mm-yyyy
    
    Returns:
        Lista de horários disponíveis
    """
    slots = get_free_slots(date)
    
    if not slots:
        return f"Não há horários disponíveis para {date}."
    
    slots_text = "\n".join([f"  • {slot}" for slot in slots])
    return f"Horários disponíveis para {date}:\n{slots_text}"


# ============================================
# INICIALIZAÇÃO DO AGENTE
# ============================================

system_prompt = """Você é a assistente virtual da clínica estética Manustetic. 

SUA PERSONALIDADE:
- Seja calorosa, acolhedora e profissional
- Use tom elegante e sofisticado, mas acessível
- Sempre confirme nomes, datas e serviços antes de agendar
- Em caso de conflito de horários, seja proativa em sugerir alternativas
- Trate clientes pelo nome quando possível

SERVIÇOS DA CLÍNICA:
1. Limpeza de Pele
2. Botox
3. Preenchimento Labial
4. Drenagem Linfática
5. Massagem Modeladora
6. Design de Sobrancelhas

INFORMAÇÕES IMPORTANTES:
- Horário de funcionamento: Segunda a Sábado, 08:00 às 19:00
- Fechado aos domingos
- Cada procedimento tem duração de 1 hora
- Formato de data: dd-mm-yyyy HH:MM

QUANDO AGENDAR:
- Sempre confirme o nome completo do cliente
- Valide a data e horário
- Confirme qual serviço
- Informe o ID do agendamento gerado

QUANDO REMARCAR OU CANCELAR:
- Solicite o ID do agendamento
- Verifique se o horário está livre antes de confirmar

MENSAGEM DE BOAS-VINDAS:
"Olá! Bem-vinda à Manustetic. Sou sua assistente virtual e estou aqui para ajudá-la a agendar seu tratamento estético com exclusividade. Como posso ajudá-la hoje?"
"""

# Criar instância do agente
agent = Agent(
    name="Assistente Manustetic",
    model=Groq(
        id="openai/gpt-oss-120b",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7
    ),
    tools=[
        schedule_appointment,
        reschedule_appointment,
        cancel_appointment,
        get_upcoming_appointments,
        suggest_free_slots
    ],
    description=system_prompt,
    instructions="""
    Você é a assistente virtual da clinica estética Manustetic.
    
    Sempre que um cliente quiser agendar:
    1. Colete o nome do cliente, data/hora e serviço
    2. Use a função schedule_appointment para criar o agendamento
    3. Se houver conflito, sugira alternativas automaticamente
    
    Sempre que um cliente quiser remarcar:
    1. Solicite o ID do agendamento
    2. Colete a nova data/hora
    3. Use a função reschedule_appointment
    
    Sempre que um cliente quiser cancelar:
    1. Solicite o ID do agendamento
    2. Use a função cancel_appointment
    
    Sempre que um cliente quiser ver agendamentos:
    1. Use a função get_upcoming_appointments
    
    Mantenha um tom elegante, caloroso e profissional em todas as interações.
    """)
