# 💆 Manustetic - Agente Virtual de Agendamento

Agente de atendimento virtual para a clínica estética Manustetic, desenvolvido com Python, Agno e Streamlit.

## ✨ Funcionalidades

- 🤖 **Assistente Inteligente**: Agente conversacional usando Groq LLM
- 📅 **Gestão de Agendamentos**: Criar, remarcar e cancelar atendimentos
- 🔍 **Consultas**: Verificar horários disponíveis e agendamentos futuros
- 💾 **Persistência**: Banco de dados DuckDB local
- 🎨 **Interface Elegante**: UI em tons de rosa com Streamlit
- 🐳 **Containerizado**: Docker pronto para deploy

## 🛠️ Tecnologias

- **Framework**: Agno
- **Modelo LLM**: Groq (openai/gpt-oss-120b)
- **Banco de Dados**: DuckDB
- **Interface**: Streamlit
- **Container**: Docker

## 📁 Estrutura do Projeto

```
agente_clinica_manustetic/
├── .env                  # Variáveis de ambiente (não versionar)
├── .env.example          # Exemplo de variáveis
├── .gitignore           # Arquivos ignorados pelo Git
├── agent.py             # Lógica do agente e ferramentas
├── app.py               # Interface Streamlit
├── docker-compose.yml   # Configuração Docker
├── Dockerfile           # Imagem Docker
├── requirements.txt     # Dependências Python
└── appointments.db      # Banco de dados DuckDB
```

## 🚀 Como Executar

### 1. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e configure sua API key:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione sua chave da API Groq:
```
GROQ_API_KEY=sua_chave_aqui
```

> Obtenha sua chave em: https://console.groq.com

### 2. Executar com Docker

```bash
docker compose up --build
```

Acesse a aplicação em: http://localhost:8501

### 3. Executar Localmente (sem Docker)

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar
streamlit run app.py
```

## 📝 Serviços Disponíveis

1. Limpeza de Pele
2. Botox
3. Preenchimento Labial
4. Drenagem Linfática
5. Massagem Modeladora
6. Design de Sobrancelhas

## 🕐 Horário de Funcionamento

- **Segunda a Sábado**: 08:00 às 19:00
- **Domingos**: Fechado

## 💬 Exemplos de Interação

### Agendar
```
"Quero agendar botox para 25-04-2026 às 14:00"
"Gostaria de marcar uma limpeza de pele amanhã às 10:00"
```

### Remarcar
```
"Preciso remarcar meu atendimento APPT-20260415143025 para 26-04-2026 às 15:00"
```

### Cancelar
```
"Quero cancelar o agendamento APPT-20260415143025"
```

### Consultar
```
"Quais meus próximos agendamentos?"
"Quais horários disponíveis para 25-04-2026?"
```

## 🔧 Ferramentas do Agente

| Ferramenta | Descrição |
|------------|-----------|
| `schedule_appointment` | Cria novo agendamento |
| `reschedule_appointment` | Remarca agendamento existente |
| `cancel_appointment` | Cancela agendamento |
| `get_upcoming_appointments` | Lista agendamentos futuros |
| `suggest_free_slots` | Mostra horários disponíveis |

## 🎨 Personalização

### Serviços
Para adicionar ou modificar serviços, edite a lista `SERVICES` em `agent.py`:

```python
SERVICES = [
    "Limpeza de Pele",
    "Botox",
    # Adicione mais serviços aqui
]
```

### Horários
Para alterar horário de funcionamento, ajuste em `agent.py`:

```python
BUSINESS_HOURS_START = 8   # 08:00
BUSINESS_HOURS_END = 19    # 19:00
```

## 📊 Banco de Dados

O banco DuckDB é criado automaticamente na primeira execução como `appointments.db`:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR | ID único (APPT-...) |
| customer_name | VARCHAR | Nome do cliente |
| appointment_time | TIMESTAMP | Data e hora do agendamento |
| service | VARCHAR | Procedimento agendado |
| status | VARCHAR | scheduled/rescheduled/cancelled |
| created_at | TIMESTAMP | Data de criação |

## 🐛 Troubleshooting

### Erro: "GROQ_API_KEY não encontrada"
- Verifique se o arquivo `.env` existe e contém a chave
- Para Docker, certifique-se de que o arquivo está no mesmo diretório do docker-compose.yml

### Erro de permissão no DuckDB
- O arquivo `appointments.db` precisa de permissões de escrita
- No Docker, o volume garante persistência dos dados

### Porta 8501 ocupada
- Altere a porta no docker-compose.yml:
```yaml
ports:
  - "8502:8501"
```

## 📄 Licença

Projeto privado - Clínica Manustetic

---
💕 **Manustetic** - Estética com exclusividade
