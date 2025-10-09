"""
roma-blackbox Interactive Showcase
Demonstrates 3 real-world use cases
"""
import streamlit as st
import asyncio
import json
from datetime import datetime
import sys
sys.path.insert(0, '..')

from roma_blackbox import BlackBoxWrapper, Policy
from roma_blackbox.pii_patterns import EnhancedPIIRedactor

st.set_page_config(
    page_title="roma-blackbox Demo",
    page_icon="🔒",
    layout="wide"
)

st.title("🔒 roma-blackbox Interactive Demo")
st.markdown("**Privacy-first monitoring for AI agents** | [GitHub](https://github.com/chiefmmorgs/roma-blackbox) | [PyPI](https://pypi.org/project/roma-blackbox/)")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    demo_mode = st.selectbox(
        "Select Demo",
        ["1. PII Scrubber", "2. Agent Wrapper", "3. API Middleware"]
    )
    
    st.divider()
    black_box = st.checkbox("Enable Black-box Mode", value=True, help="Hide execution traces")
    redact_pii = st.checkbox("Enable PII Redaction", value=True, help="Redact sensitive data")
    keep_hashes = st.checkbox("Keep Hashes", value=True, help="Store SHA256 hashes")
    
    st.divider()
    st.caption("roma-blackbox v0.3.2")

# Demo 1: PII Scrubber
if demo_mode == "1. PII Scrubber":
    st.header("Demo 1: PII Scrubber")
    st.markdown("**Use Case**: Clean customer support chat logs before storing or analyzing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Input (Raw Chat Log)")
        sample_text = """Customer Support Chat - Session #12345
Timestamp: 2024-10-06 14:30:22

Agent: Hello! How can I help you today?
Customer: Hi, I need help with my account. My email is john.doe@example.com
Agent: Thank you! I've pulled up your account. Can you verify your phone?
Customer: Sure, it's 555-123-4567
Agent: Perfect. I also see your SSN ending in 1234. Is that correct?
Customer: Yes, my full SSN is 123-45-6789
Agent: Great! Your account shows a payment from card ****-1234. 
Customer: That's my card 4532-1234-5678-9010
Agent: I'll process the refund to that card.
Customer: Thanks! My crypto wallet is 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
Agent: Noted. Anything else?
Customer: No, that's all. My IP is 192.168.1.100 by the way.
Agent: Perfect, you're all set!
"""
        
        user_input = st.text_area(
            "Enter text with PII",
            value=sample_text,
            height=400,
            help="Try adding emails, phone numbers, SSNs, credit cards, etc."
        )
        
        if st.button("🔍 Scan for PII", type="primary"):
            redactor = EnhancedPIIRedactor()
            found_pii = redactor.scan(user_input)
            
            st.success(f"Found {len(found_pii)} PII types")
            for pii_type, count in found_pii.items():
                st.write(f"- **{pii_type}**: {count} occurrence(s)")
    
    with col2:
        st.subheader("✅ Output (Redacted)")
        
        if st.button("🔒 Redact PII", type="primary"):
            redactor = EnhancedPIIRedactor()
            redacted = redactor.redact(user_input)
            
            st.text_area(
                "Redacted text",
                value=redacted,
                height=400,
                help="All PII replaced with type markers"
            )
            
            # Show what changed
            with st.expander("📊 What Changed"):
                original_lines = user_input.split('\n')
                redacted_lines = redacted.split('\n')
                
                changes = 0
                for i, (orig, red) in enumerate(zip(original_lines, redacted_lines)):
                    if orig != red:
                        changes += 1
                        st.markdown(f"**Line {i+1}:**")
                        st.code(f"- {orig}", language=None)
                        st.code(f"+ {red}", language=None)
                
                st.metric("Lines Modified", changes)

# Demo 2: Agent Wrapper
elif demo_mode == "2. Agent Wrapper":
    st.header("Demo 2: Agent Wrapper")
    st.markdown("**Use Case**: Monitor AI agents without exposing execution traces")
    
    # Mock agent
    class WeatherAgent:
        async def run(self, task: str, **kwargs):
            city = kwargs.get('city', 'Unknown')
            
            # Simulate detailed traces
            traces = [
                f"[{datetime.now().isoformat()}] WeatherAgent initialized",
                f"[API] Calling OpenWeatherMap for {city}",
                f"[API] API Key: sk_live_abc123... (first 10 chars)",
                f"[DB] Querying user preferences database",
                f"[DB] Retrieved email: user@example.com from profile",
                f"[CALC] Converting temperature Kelvin -> Celsius",
                f"[CALC] Applying user timezone offset",
                f"[FORMAT] Formatting response for delivery",
            ]
            
            result = {
                "city": city,
                "temperature": 25,
                "condition": "Sunny",
                "humidity": 65,
                "recommendation": "Great day for outdoor activities!"
            }
            
            return {
                "status": "success",
                "result": result,
                "traces": traces
            }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 Normal Agent Execution")
        
        city = st.text_input("Enter city", value="Tokyo", key="city_normal")
        
        if st.button("Run Agent (Normal)", type="secondary"):
            agent = WeatherAgent()
            
            with st.spinner("Running agent..."):
                result = asyncio.run(agent.run(task="get weather", city=city))
            
            st.json(result, expanded=True)
            
            st.warning("⚠️ Traces expose:")
            st.markdown("""
            - API keys
            - Database queries
            - User emails
            - Internal logic
            """)
    
    with col2:
        st.subheader("🔒 Wrapped with roma-blackbox")
        
        city2 = st.text_input("Enter city", value="Tokyo", key="city_wrapped")
        
        if st.button("Run Agent (Wrapped)", type="primary"):
            agent = WeatherAgent()
            
            policy = Policy(
                black_box=black_box,
            )
            
            wrapped = BlackBoxWrapper(
                agent,
                policy,
                storage="memory",
                use_enhanced_pii=redact_pii
            )
            
            with st.spinner("Running wrapped agent..."):
                result = asyncio.run(wrapped.run(
                    request_id=f"weather_{datetime.now().timestamp()}",
                    task="get weather",
                    city=city2
                ))
            
            output = {
                "status": result.status,
                "result": result.result,
                "traces": result.traces,
                "input_hash": result.input_hash if keep_hashes else "disabled",
                "output_hash": result.output_hash if keep_hashes else "disabled"
            }
            
            st.json(output, expanded=True)
            
            st.success("✅ Protected:")
            if black_box:
                st.markdown("- ✅ Traces hidden")
            if redact_pii:
                st.markdown("- ✅ PII redacted")
            if keep_hashes:
                st.markdown("- ✅ Hashes stored for audit")

# Demo 3: API Middleware
elif demo_mode == "3. API Middleware":
    st.header("Demo 3: API Middleware")
    st.markdown("**Use Case**: Clean API requests/responses before logging")
    
    # Mock API handler
    class APIHandler:
        async def run(self, task: str, **kwargs):
            method = kwargs.get('method', 'POST')
            endpoint = kwargs.get('endpoint', '/api/users')
            payload = kwargs.get('payload', {})
            
            traces = [
                f"[HTTP] {method} {endpoint}",
                f"[AUTH] Validating API key: {payload.get('api_key', 'N/A')[:20]}...",
                f"[VALIDATION] Checking request body",
                f"[DB] INSERT INTO users (email, phone, ssn)",
                f"[RESPONSE] 201 Created",
            ]
            
            response = {
                "user_id": "usr_abc123",
                "email": payload.get('email', 'unknown'),
                "phone": payload.get('phone', 'unknown'),
                "created_at": datetime.now().isoformat(),
                "message": f"User {payload.get('email')} created successfully"
            }
            
            return {
                "status": "success",
                "result": response,
                "traces": traces
            }
    
    st.subheader("📨 Sample API Request")
    
    sample_request = {
        "method": "POST",
        "endpoint": "/api/users",
        "headers": {
            "Authorization": "Bearer sk_live_abc123def456ghi789",
            "Content-Type": "application/json"
        },
        "body": {
            "email": "newuser@company.com",
            "phone": "+1-555-123-4567",
            "ssn": "123-45-6789",
            "address": "123 Main St, Springfield",
            "credit_card": "4532-1234-5678-9010"
        }
    }
    
    user_request = st.text_area(
        "API Request JSON",
        value=json.dumps(sample_request, indent=2),
        height=250
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Normal Logging")
        
        if st.button("Process Request (Normal)", type="secondary"):
            try:
                request_data = json.loads(user_request)
                handler = APIHandler()
                
                result = asyncio.run(handler.run(
                    task="handle api request",
                    **request_data.get('body', {})
                ))
                
                st.json(result, expanded=True)
                st.error("⚠️ Sensitive data in logs!")
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.subheader("🔒 Protected Logging")
        
        if st.button("Process Request (Protected)", type="primary"):
            try:
                request_data = json.loads(user_request)
                handler = APIHandler()
                
                policy = Policy(black_box=black_box)
                wrapped = BlackBoxWrapper(
                    handler,
                    policy,
                    storage="memory",
                    use_enhanced_pii=redact_pii
                )
                
                result = asyncio.run(wrapped.run(
                    request_id=f"api_{datetime.now().timestamp()}",
                    task="handle api request",
                    **request_data.get('body', {})
                ))
                
                output = {
                    "status": result.status,
                    "result": result.result,
                    "traces": result.traces,
                }
                
                st.json(output, expanded=True)
                st.success("✅ Safe to store in logs!")
                
            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.divider()
st.markdown("""
### 🎯 Key Takeaways

1. **PII Scrubber**: Automatically detect and redact 14+ types of sensitive data
2. **Agent Wrapper**: Hide internal execution traces while preserving results
3. **API Middleware**: Clean requests/responses before logging or storage

**Installation**: `pip install roma-blackbox`  
**Docs**: [GitHub README](https://github.com/chiefmmorgs/roma-blackbox)
""")
