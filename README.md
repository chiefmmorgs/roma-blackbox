Privacy-first monitoring for AI agent systems. Strip execution traces, redact PII, and maintain compliance while running multi-agent workflows.


roma-blackbox wraps your agents to:
- Hide internal execution traces (black-box mode)
- Redact PII from inputs/outputs (14 pattern types)
- Store only outcomes with cryptographic attestations
- Preserve results while protecting process

## Installation 
```bash
pip install roma-blackbox
```
With optional features:
```bash
pip install roma-blackbox[langchain]  # LangChain integration
pip install roma-blackbox[all]        # Everything
```
Quick Start
cd ~/roma-blackbox/demo

# roma-blackbox Interactive Demo

Three interactive use-case demonstrations showing what roma-blackbox does.

## Demos Included

1. **PII Scrubber**: Redact emails, SSNs, credit cards, etc. from text
2. **Agent Wrapper**: Hide AI agent execution traces while preserving results
3. **API Middleware**: Clean API requests/responses before logging

## Option 1: Test with Published Package (User Experience)

This tests the demo using the published PyPI package, exactly as end users would experience it.
```bash
# Create clean test environment
mkdir roma-demo-test
cd roma-demo-test
```
# Download demo files
```
curl -O https://raw.githubusercontent.com/chiefmmorgs/roma-blackbox/master/demo/showcase.py
curl -O https://raw.githubusercontent.com/chiefmmorgs/roma-blackbox/master/demo/requirements.txt
```
# Setup and run
```
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run showcase.py
Open http://localhost:8501 in your browser.
```

Basic Usage

```python
from roma_blackbox import BlackBoxWrapper, Policy

# Your agent must have an async run() method
class MyAgent:
    async def run(self, task: str, **kwargs):
        return {
            "status": "success",
            "result": "some output",
            "traces": ["step1", "step2"]  # Will be stripped
        }

# Wrap it
wrapped = BlackBoxWrapper(
    MyAgent(),
    Policy(black_box=True),
    storage="memory"
)

# Use it
result = await wrapped.run(
    request_id="req_001",
    task="user query"
)

print(result.status)      # "success"
print(result.result)      # "some output"
print(result.traces)      # None (hidden in black-box mode)
```
With PII Redaction
```python
wrapped = BlackBoxWrapper(
    agent,
    Policy(black_box=True),
    storage="memory",
    use_enhanced_pii=True  # Enables PII redaction
)

result = await wrapped.run(
    request_id="req_002",
    task="Email user@example.com about order"
)

# result.result will have [EMAIL] instead of actual email
```
Integrating Your Agents

roma-blackbox doesn't automatically work with every agent. You need to write a thin adapter if your agents use different methods.

If Your Agent Uses .execute()
```python
import asyncio

class AgentAdapter:
    def __init__(self, your_agent):
        self.agent = your_agent
    
    async def run(self, task: str, **kwargs):
        # Convert sync to async
        result = await asyncio.to_thread(
            self.agent.execute, 
            **kwargs
        )
        
        return {
            "status": "success",
            "result": result,
            "traces": [f"Executed {self.agent.__class__.__name__}"]
        }

# Use it
adapter = AgentAdapter(your_agent)
wrapped = BlackBoxWrapper(adapter, Policy(black_box=True))
```
If Your Agent Is Async Already
```python
class AsyncAdapter:
    def __init__(self, your_agent):
        self.agent = your_agent
    
    async def run(self, task: str, **kwargs):
        result = await self.agent.your_method(**kwargs)
        return {"status": "success", "result": result}

wrapped = BlackBoxWrapper(AsyncAdapter(agent), Policy(black_box=True))
```
Multi-Agent Systems
```python
class OrchestratorAdapter:
    def __init__(self, planner, executor):
        self.planner = planner
        self.executor = executor
    
    async def run(self, task: str, **kwargs):
        plan = self.planner.plan(task)
        result = self.executor.execute(plan)
        
        return {
            "status": "success",
            "result": result,
            "traces": [
                f"Planned: {plan}",
                f"Executed: {result}"
            ]
        }
```
LangChain Integration
Built-in support for LangChain agents:
```python
from langchain.agents import create_openai_functions_agent
from roma_blackbox.integrations import LangChainWrapper

agent = create_openai_functions_agent(llm, tools, prompt)

wrapped = LangChainWrapper(
    agent,
    policy=Policy(black_box=True),
    storage="memory"
)

result = wrapped.invoke({"input": "book a flight to NYC"})
# Traces stripped, PII redacted, only outcome stored
```
Policy Configuration

```python
from roma_blackbox import Policy

policy = Policy(
    black_box=True,              # Hide traces
    keep_hashes=True,            # Store SHA256 hashes of I/O
    max_cost_cents=100.0,        # Cost limit per request
    request_timeout_seconds=300, # Timeout
    break_glass_request_ids=[],  # Override for debugging
)
```
PII Detection Patterns

Automatically redacts 14 types:

Email addresses → [EMAIL]

SSNs → [SSN]

Credit cards → [CREDIT_CARD]

Phone numbers → [PHONE]

IP addresses → [IP_ADDRESS]

API keys (AWS, GitHub, generic) → [API_KEY]

Crypto addresses (Bitcoin, Ethereum) → [BTC_ADDRESS]

And more...


**Custom Patterns**
```python
from roma_blackbox.pii_patterns import EnhancedPIIRedactor, PIIPattern

custom_pattern = PIIPattern(
    "employee_id",
    r'\bEMP-\d{6}\b',
    "[EMPLOYEE_ID]"
)

redactor = EnhancedPIIRedactor(custom_patterns=[custom_pattern])
```
Storage Backends
```python
# In-memory (default)
wrapped = BlackBoxWrapper(agent, policy, storage="memory")

# PostgreSQL
wrapped = BlackBoxWrapper(agent, policy, storage="postgres")
```
Examples
See examples/ directory:

basic_usage.py - Simple agent wrapping

langchain_example.py - LangChain integration

pii_detection_example.py - PII redaction demo

adapters/ - Adapter patterns for different agent types

Testing
```bash
pytest tests/ -v
```
Real-World Example
```python
# Your ROMA travel planning agent
class WeatherAgent:
    def execute(self, destination):
        # Makes API call to OpenWeatherMap
        return {"temp": 25, "condition": "sunny"}

# Adapt it
class WeatherAdapter:
    def __init__(self, agent):
        self.agent = agent
    
    async def run(self, task: str, destination=None):
        result = self.agent.execute(destination)
        return {
            "status": "success",
            "result": result,
            "traces": [f"API call to OpenWeatherMap for {destination}"]
        }

# Wrap it
wrapped = BlackBoxWrapper(
    WeatherAdapter(WeatherAgent()),
    Policy(black_box=True),
    storage="memory",
    use_enhanced_pii=True
)

# Use it
result = await wrapped.run(
    request_id="weather_001",
    task="Get weather",
    destination="Tokyo"
)
# Traces hidden, outcome stored, API keys protected
```
**Key Concepts**
Black-box mode: Agent execution details are hidden. Only inputs, outputs, and outcomes are preserved.

Break-glass: Override black-box mode for specific request IDs during debugging.

Attestations: Cryptographic proofs linking requests to code versions and policies.

Storage: Outcomes are stored (memory or PostgreSQL) for auditability without exposing traces.

W

FAQ

Q: Do I need to modify my existing agents?

A: Write a thin adapter (see examples above). 5-10 lines of code.

Q: Does it work with [framework X]?

A: If you can write an adapter that provides async run(), yes.

Q: What if my agent is synchronous?

A: Use asyncio.to_thread() in your adapter (see examples).

Q: Does it slow down my agents?

A: Adds ~10ms overhead for wrapping + storage. PII redaction adds ~1-5ms depending on data size.

Q: Can I disable PII redaction?

A: Yes: use_enhanced_pii=False in BlackBoxWrapper.

Contributing

Issues and PRs welcome at https://github.com/chiefmmorgs/roma-blackbox



## 🚀 VPS/Server Installation Guide

### Common Issues and Solutions

#### Issue 1: `pip` command not found

**Problem:**
```bash
root@server:~# pip install roma-blackbox
Command 'pip' not found
```
Solution:
```bashapt update
apt install python3-pip python3-venv -y
```
Then use pip3 instead of pip.

Issue 2: externally-managed-environment error
Problem:
bashroot@server:~# pip3 install roma-blackbox
error: externally-managed-environment
× This environment is externally managed
Solution: Use a virtual environment (best practice for servers):
```bash# Create project directory
mkdir ~/roma-blackbox-app
cd ~/roma-blackbox-app

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install
pip install roma-blackbox
```
# Verify
python -c "from roma_blackbox import BlackBoxWrapper; print('✓ Works!')"
Each time you SSH in, activate the venv:
```bash
cd ~/roma-blackbox-app
source venv/bin/activate
```
Issue 3: python3-venv not available

Problem:

```bash
python3 -m venv venv
```
The virtual environment was not created successfully because ensurepip is not available.

Solution:
```bash
# Install python3-venv package
apt install python3.12-venv -y

# Or for other Python versions:
apt install python3-venv -y

# Now create venv
python3 -m venv venv
source venv/bin/activate
```
Issue 4: Streamlit demo not accessible from browser

Problem:

This site can't be reached

http://0.0.0.0:8501/ - ERR_ADDRESS_INVALID

Solution:

Find your server's public IP:

```bash
curl ifconfig.me
# Example output: 77.90.19.203
```
Open firewall port:

```bash
# UFW (Ubuntu/Debian)
ufw allow 8501/tcp

# Or iptables
iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
```
Run streamlit with correct binding:

```bash
cd ~/roma-blackbox-app
source venv/bin/activate
pip install streamlit

# Download demo
curl -O https://raw.githubusercontent.com/chiefmmorgs/roma-blackbox/master/demo/showcase.py

# Run (bind to all interfaces)
streamlit run showcase.py --server.address 0.0.0.0 --server.port 8501
```
Access from browser using your PUBLIC IP:

http://77.90.19.203:8501

(Replace with your actual IP from step 1)

Don't use 0.0.0.0 in the browser - that's the server bind address. Use your real IP.

Complete VPS Setup (Ubuntu/Debian)
```bash
# 1. Install dependencies
apt update
apt install python3-pip python3-venv -y

# 2. Create project
mkdir ~/roma-blackbox-app
cd ~/roma-blackbox-app

# 3. Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install roma-blackbox
pip install roma-blackbox

# 5. Test installation
python -c "from roma_blackbox import BlackBoxWrapper, Policy; print('✓ Installed')"

# 6. (Optional) Run demo
pip install streamlit
curl -O https://raw.githubusercontent.com/chiefmmorgs/roma-blackbox/master/demo/showcase.py
ufw allow 8501/tcp
streamlit run showcase.py --server.address 0.0.0.0 --server.port 8501

# Access at: http://YOUR_SERVER_IP:8501

Production Deployment Tips
1. Run as systemd service:
bash# Create service file
cat > /etc/systemd/system/roma-demo.service << 'SYSTEMD'
[Unit]
Description=roma-blackbox Demo
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/roma-blackbox-app
Environment="PATH=/root/roma-blackbox-app/venv/bin"
ExecStart=/root/roma-blackbox-app/venv/bin/streamlit run showcase.py --server.address 0.0.0.0 --server.port 8501
Restart=always
```
[Install]

WantedBy=multi-user.target

SYSTEMD
```

# Enable and start
systemctl daemon-reload
systemctl enable roma-demo
systemctl start roma-demo

# Check status
systemctl status roma-demo
2. Use nginx reverse proxy (optional):
bashapt install nginx -y

cat > /etc/nginx/sites-available/roma-demo << 'NGINX'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX

ln -s /etc/nginx/sites-available/roma-demo /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
Now access at http://your-domain.com instead of http://IP:8501
3. Environment variables for production:
bash# Create .env file
cat > ~/roma-blackbox-app/.env << 'ENV'
POSTGRES_URL=postgresql://user:pass@localhost/dbname
OPENWEATHER_API_KEY=your_key_here
ENV

# Load in your app
pip install python-dotenv
pythonfrom dotenv import load_dotenv
load_dotenv()
```
Security Notes

⚠️ Never run production apps as root (create dedicated user)

⚠️ Use environment variables for secrets, not hardcoded values

⚠️ Enable HTTPS with Let's Encrypt for public demos

⚠️ Restrict firewall to only necessary ports

⚠️ Keep packages updated: pip install --upgrade roma-blackbox
