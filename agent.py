"""Agente Manustetic - Versão com Session ID"""
import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.toolkit import Toolkit
from agno.tools import tool

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('manustetic.log'), logging.StreamHandler()])
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS appointments (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, service TEXT, appointment_date TEXT, appointment_time TEXT, phone TEXT, status TEXT DEFAULT 'ativo', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, email TEXT, birthday TEXT, accept_marketing BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_visit TIMESTAMP, total_appointments INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()
    logger.info("Banco de dados inicializado")

def parse_natural_date(date_str):
    if not date_str:
        return None
    s = str(date_str).lower().strip()
    today = now_saopaulo().date()
    if s in ["hoje", "hj"]:
        return today.isoformat()
    if s in ["amanha", "amanhã"]:
        return (today + timedelta(days=1)).isoformat()
    if s in ["depois de amanha", "depois de amanhã"]:
        return (today + timedelta(days=2)).isoformat()
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m", "%d-%m"]:
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
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        rs = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        re = rs + timedelta(minutes=duration)
        c.execute("SELECT appointment_time, service FROM appointments WHERE appointment_date = ? AND status != 'cancelado'", (date_str,))
        rows = c.fetchall()
        conn.close()
        for t, s in rows:
            es = datetime.strptime(f"{date_str} {t}", "%Y-%m-%d %H:%M")
            ee = es + timedelta(minutes=SERVICES.get(s, {}).get("duration", 60))
            if rs < ee and re > es:
                return True
        return False
    except Exception as e:
        logger.error(f"Erro conflito: {e}")
        return False

class ManusteticTools(Toolkit):
    def __init__(self):
        super().__init__(name="manustetic_tools")
        self.register(self.add_appointment)
        self.register(self.list_appointments)
        self.register(self.get_available_slots)
        self.register(self.cancel_appointment)
        self.register(self.get_current_datetime)

    @tool
    def add_appointment(self, customer_name: str, service: str, date: str = None, time: str = None, appointment_date: str = None, appointment_time: str = None, phone: str = None) -> str:
        """Agenda um novo compromisso. Delega para ScheduleAgent verificar e criar."""
        try:
            fd = date or appointment_date
            ft = time or appointment_time
            if not fd or not ft:
                return "Preciso da data e do horário."
            
            # Delega verificação e criação pro ScheduleAgent
            schedule_agent = create_schedule_agent()
            result = schedule_agent.run(
                f"Crie agendamento para {customer_name}, serviço {service}, dia {fd}, horário {ft}, telefone {phone}"
            )
            
            content = result.content if hasattr(result, 'content') else str(result)
            
            # Se o ScheduleAgent confirmou, loga e retorna
            if "confirmado" in content.lower() or "sucesso" in content.lower():
                pd = parse_natural_date(fd)
                logger.info(f"Agendado: {customer_name}, {service}, {pd} {ft}")
            
            return content
            
        except Exception as e:
            logger.error(f"Erro: {e}")
            return "Erro ao criar agendamento. Tente novamente."

    @tool
    def list_appointments(self, customer_name: str = None) -> str:
        """Lista agendamentos."""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            today = now_saopaulo().date().isoformat()
            if customer_name:
                c.execute("SELECT * FROM appointments WHERE customer_name LIKE ? AND appointment_date >= ? AND status != 'cancelado' ORDER BY appointment_date", (f"%{customer_name}%", today))
            else:
                c.execute("SELECT * FROM appointments WHERE appointment_date >= ? AND status != 'cancelado' ORDER BY appointment_date", (today,))
            rows = c.fetchall()
            conn.close()
            if not rows:
                return "Nenhum agendamento encontrado."
            r = "📅 Agendamentos:\n\n"
            for a in rows:
                r += f"• {a[1]} - {a[2]} em {a[3]} às {a[4]}\n"
            return r
        except Exception as e:
            return f"Erro: {e}"

    @tool
    def get_available_slots(self, date: str = None, appointment_date: str = None) -> str:
        """Horários disponíveis."""
        try:
            fd = date or appointment_date
            if not fd:
                return "Informe uma data."
            pd = parse_natural_date(fd)
            if not pd:
                return f"Data '{fd}' inválida."
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT appointment_time FROM appointments WHERE appointment_date = ? AND status != 'cancelado'", (pd,))
            booked = [r[0] for r in c.fetchall()]
            conn.close()
            all_slots = [f"{h:02d}:00" for h in range(8, 19)]
            avail = [s for s in all_slots if s not in booked]
            if not avail:
                return f"Sem horários para {pd}."
            return f"Horários em {pd}:\n" + "\n".join([f"• {s}" for s in avail])
        except Exception as e:
            return f"Erro: {e}"

    @tool
    def cancel_appointment(self, customer_name: str, date: str = None, appointment_date: str = None) -> str:
        """Cancela agendamento."""
        try:
            fd = date or appointment_date
            if not fd:
                return "Preciso da data."
            pd = parse_natural_date(fd) or fd
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE appointments SET status = 'cancelado' WHERE customer_name LIKE ? AND appointment_date = ? AND status = 'ativo'", (f"%{customer_name}%", pd))
            conn.commit()
            updated = c.rowcount
            conn.close()
            return "Cancelado! ✅" if updated > 0 else "Não encontrei agendamento ativo."
        except Exception as e:
            return f"Erro: {e}"

    @tool
    def get_current_datetime(self) -> str:
        """Retorna a data e hora atual no fuso America/Sao_Paulo.
        
        Returns:
            Data e hora atual no formato YYYY-MM-DD HH:MM:SS
        """
        return now_saopaulo().strftime('%Y-%m-%d %H:%M:%S')

    @tool
    def delegate_to_schedule_agent(self, operation: str, customer_name: str = None, date: str = None, time: str = None, new_date: str = None, new_time: str = None, service: str = None) -> str:
        """Delega operações de agenda para o ScheduleAgent especializado.
        
        Args:
            operation: Tipo de operação ('check', 'cancel', 'reschedule', 'list_day')
            customer_name: Nome do cliente
            date: Data atual/original
            time: Horário atual/original
            new_date: Nova data (para reagendamento)
            new_time: Novo horário (para reagendamento)
            service: Nome do serviço
        
        Returns:
            Resultado da operação da agenda
        """
        try:
            schedule_agent = create_schedule_agent()
            
            if operation == "check":
                result = schedule_agent.run(f"Verifique disponibilidade para {customer_name} no dia {date} às {time} para o serviço {service}")
                return result.content if hasattr(result, 'content') else str(result)
            
            elif operation == "cancel":
                result = schedule_agent.run(f"Cancele o agendamento de {customer_name} no dia {date}")
                return result.content if hasattr(result, 'content') else str(result)
            
            elif operation == "reschedule":
                result = schedule_agent.run(f"Reagende {customer_name} do dia {date} às {time} para {new_date} às {new_time}")
                return result.content if hasattr(result, 'content') else str(result)
            
            elif operation == "list_day":
                result = schedule_agent.run(f"Liste todos os agendamentos do dia {date}")
                return result.content if hasattr(result, 'content') else str(result)
            
            else:
                return f"Operação '{operation}' não reconhecida."
        except Exception as e:
            logger.error(f"Erro delegação: {e}")
            return f"Erro ao processar operação: {e}"

system_prompt = f"""Você é a assistente virtual da Manu Santos Esthetic.

PERSONALIDADE:
- Calorosa, acolhedora e profissional
- Use emojis sutilmente (🌿, ✨, 💚)
- Seja CONCISA nas respostas
- Trate as clientes pelo nome

SERVIÇOS:
{chr(10).join([f"• {n}: {i['price']} ({i['duration']} min)" for n, i in SERVICES.items()])}

HORÁRIO: Segunda a Sábado, 08:00 às 19:00
WHATSAPP: +55 11 95186-3253

REGRAS:
1. Pergunte o nome na PRIMEIRA interação
2. MANTENHA o nome e contexto durante TODA conversa
3. Confirme dados antes de agendar
4. Use add_appointment para criar agendamentos (ela delega automaticamente para o ScheduleAgent)
5. Para cancelar: use cancel_appointment do ManusteticTools
6. Para ver disponibilidade: use get_available_slots
7. NÃO mostre erros técnicos ao cliente
8. NUNCA esqueça informações já fornecidas
9. Para obter a data/hora atual: use get_current_datetime (chame sempre que precisar da data/hora real)
10. IMPORTANTE: Antes de qualquer resposta que envolva data ou hora, SEMPRE chame a tool get_current_datetime para obter a data atual. NUNCA assuma a data — sempre consulte a tool.
"""

class ScheduleAgentTools(Toolkit):
    """Ferramentas especializadas para gestão de agenda."""
    
    def __init__(self):
        super().__init__(name="schedule_tools")
        self.register(self.check_availability)
        self.register(self.create_appointment)
        self.register(self.cancel_appointment)
        self.register(self.reschedule_appointment)
        self.register(self.get_appointments_by_date)

    @tool
    def check_availability(self, date: str, time: str, service: str = None, duration: int = 60) -> str:
        """Verifica se um horário está disponível na agenda.
        
        Args:
            date: Data no formato YYYY-MM-DD ou natural (hoje, amanhã)
            time: Horário no formato HH:MM
            service: Nome do serviço (opcional)
            duration: Duração em minutos
        
        Returns:
            JSON com disponibilidade e conflitos se houver
        """
        try:
            pd = parse_natural_date(date) or date
            if not pd:
                return json.dumps({"available": False, "error": f"Data '{date}' inválida"})
            
            # Verifica horário de expediente
            try:
                h = int(time.split(":")[0])
                if h < 8 or h >= 19:
                    return json.dumps({"available": False, "error": "Horário fora do expediente (08:00 às 19:00)"})
            except:
                return json.dumps({"available": False, "error": f"Horário '{time}' inválido"})
            
            # Verifica conflito
            has_conflict = check_time_conflict(pd, time, duration)
            
            if has_conflict:
                # Busca conflitos para informar
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT customer_name, service, appointment_time FROM appointments WHERE appointment_date = ? AND status != 'cancelado'", (pd,))
                conflicts = c.fetchall()
                conn.close()
                
                return json.dumps({
                    "available": False,
                    "conflicts": [{"client": c[0], "service": c[1], "time": c[2]} for c in conflicts]
                })
            
            return json.dumps({"available": True, "date": pd, "time": time})
            
        except Exception as e:
            logger.error(f"Erro check_availability: {e}")
            return json.dumps({"available": False, "error": str(e)})

    @tool
    def create_appointment(self, customer_name: str, service: str, date: str, time: str, phone: str = None) -> str:
        """Cria um novo agendamento após verificar disponibilidade.
        
        Args:
            customer_name: Nome do cliente
            service: Nome do serviço
            date: Data do agendamento
            time: Horário do agendamento
            phone: Telefone (opcional)
        
        Returns:
            Confirmação ou erro
        """
        try:
            pd = parse_natural_date(date) or date
            if not pd:
                return f"Data '{date}' inválida."
            
            if service not in SERVICE_NAMES:
                return f"Serviço '{service}' não encontrado. Disponíveis: {', '.join(SERVICE_NAMES)}"
            
            # Verifica horário de expediente
            try:
                h = int(time.split(":")[0])
                if h < 8 or h >= 19:
                    return "Horário fora do expediente (08:00 às 19:00)."
            except:
                return f"Horário '{time}' inválido."
            
            # Verifica conflito
            duration = SERVICES[service]["duration"]
            has_conflict = check_time_conflict(pd, time, duration)
            
            if has_conflict:
                return f"❌ Já existe agendamento em {time}. Posso verificar outros horários."
            
            # Cria o agendamento
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO appointments (customer_name, service, appointment_date, appointment_time, phone, status) VALUES (?, ?, ?, ?, ?, 'ativo')", 
                     (customer_name, service, pd, time, phone))
            conn.commit()
            conn.close()
            
            return f"Agendamento confirmado! ✅\n\nCliente: {customer_name}\nServiço: {service}\nData: {pd}\nHorário: {time}\n\nAguardamos você! 🌿"
            
        except Exception as e:
            logger.error(f"Erro create_appointment: {e}")
            return f"Erro ao criar agendamento: {e}"

    @tool
    def cancel_appointment(self, customer_name: str, date: str) -> str:
        """Cancela um agendamento ativo.
        
        Args:
            customer_name: Nome do cliente
            date: Data do agendamento
        
        Returns:
            Resultado do cancelamento
        """
        try:
            pd = parse_natural_date(date) or date
            if not pd:
                return f"Data '{date}' inválida."
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Busca o agendamento antes de cancelar
            c.execute("SELECT id, service, appointment_time FROM appointments WHERE customer_name LIKE ? AND appointment_date = ? AND status = 'ativo'", 
                     (f"%{customer_name}%", pd))
            appt = c.fetchone()
            
            if not appt:
                conn.close()
                return f"Não encontrei agendamento ativo para {customer_name} em {pd}."
            
            # Cancela
            c.execute("UPDATE appointments SET status = 'cancelado' WHERE id = ?", (appt[0],))
            conn.commit()
            conn.close()
            
            return f"✅ Agendamento cancelado: {customer_name} - {appt[1]} em {pd} às {appt[2]}"
            
        except Exception as e:
            logger.error(f"Erro cancel_appointment: {e}")
            return f"Erro ao cancelar: {e}"

    @tool
    def reschedule_appointment(self, customer_name: str, old_date: str, old_time: str = None, new_date: str = None, new_time: str = None) -> str:
        """Reagenda um compromisso para outro dia/horário.
        
        Args:
            customer_name: Nome do cliente
            old_date: Data atual do agendamento
            old_time: Horário atual (opcional, para identificação)
            new_date: Nova data
            new_time: Novo horário
        
        Returns:
            Resultado do reagendamento
        """
        try:
            pd_old = parse_natural_date(old_date) or old_date
            pd_new = parse_natural_date(new_date) or new_date
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Busca agendamento atual
            query = "SELECT id, service, appointment_time FROM appointments WHERE customer_name LIKE ? AND appointment_date = ? AND status = 'ativo'"
            params = [f"%{customer_name}%", pd_old]
            if old_time:
                query += " AND appointment_time = ?"
                params.append(old_time)
            
            c.execute(query, params)
            appt = c.fetchone()
            
            if not appt:
                conn.close()
                return f"Agendamento não encontrado para {customer_name} em {pd_old}."
            
            appt_id, service, current_time = appt
            duration = SERVICES.get(service, {}).get("duration", 60)
            
            # Verifica disponibilidade no novo horário
            has_conflict = check_time_conflict(pd_new, new_time, duration)
            if has_conflict:
                conn.close()
                return f"❌ Horário {new_time} em {pd_new} já está ocupado."
            
            # Atualiza o agendamento
            c.execute("UPDATE appointments SET appointment_date = ?, appointment_time = ? WHERE id = ?", 
                     (pd_new, new_time, appt_id))
            conn.commit()
            conn.close()
            
            return f"✅ Reagendado com sucesso!\nDe: {pd_old} às {current_time}\nPara: {pd_new} às {new_time}"
            
        except Exception as e:
            logger.error(f"Erro reschedule_appointment: {e}")
            return f"Erro ao reagendar: {e}"

    @tool
    def get_appointments_by_date(self, date: str) -> str:
        """Lista todos os agendamentos de uma data específica.
        
        Args:
            date: Data para consulta
        
        Returns:
            Lista de agendamentos do dia
        """
        try:
            pd = parse_natural_date(date) or date
            if not pd:
                return f"Data '{date}' inválida."
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT customer_name, service, appointment_time, status FROM appointments WHERE appointment_date = ? ORDER BY appointment_time", (pd,))
            rows = c.fetchall()
            conn.close()
            
            if not rows:
                return f"Nenhum agendamento encontrado para {pd}."
            
            result = f"📅 Agendamentos para {pd}:\n\n"
            for r in rows:
                status_icon = "✅" if r[3] == "ativo" else "❌"
                result += f"{status_icon} {r[2]} - {r[0]} ({r[1]})\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Erro get_appointments_by_date: {e}")
            return f"Erro ao consultar: {e}"

schedule_agent_system_prompt = """Você é o ScheduleAgent - Especialista em Gestão de Agenda da Manu Santos Esthetic.

FUNÇÃO:
Analisar e manipular a agenda de agendamentos. Você verifica conflitos, cancela e reagenda compromissos.

REGRAS:
1. Verifique SEMPRE se há conflito antes de qualquer operação
2. Para cancelar: use cancel_appointment - marca como 'cancelado'
3. Para reagendar: primeiro cancele o antigo, depois verifique disponibilidade no novo horário
4. Retorne respostas claras sobre o resultado da operação
5. NUNCA permita duplicidade de horários

OPERAÇÕES SUPORTADAS:
- check_availability: verifica se dia/horário está livre
- cancel_appointment: cancela agendamento ativo
- reschedule_appointment: reagenda para novo dia/horário
- get_appointments_by_date: lista agendamentos de um dia específico
"""

def create_schedule_agent():
    """Cria o agente especialista em agenda."""
    return Agent(
        name="ScheduleAgent",
        model=Groq(
            id="openai/gpt-oss-120b",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.3,
            max_tokens=1024
        ),
        tools=[ScheduleAgentTools()],
        description=schedule_agent_system_prompt,
        add_history_to_context=False
    )

def create_agent(session_id: str = None):
    return Agent(
        name="Manustetic",
        model=Groq(
            id="openai/gpt-oss-120b",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.7,
            max_tokens=1024
        ),
        tools=[ManusteticTools()],
        description=system_prompt,
        session_id=session_id,
        add_history_to_context=True,
        num_history_runs=8
    )

init_db()
logger.info("Agente Manustetic inicializado com sucesso")
