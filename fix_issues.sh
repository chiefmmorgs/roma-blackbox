#!/bin/bash
# Fix 1: Add asyncio import to tests
sed -i '1i import asyncio' tests/test_blackbox.py

# Fix 2: Update datetime in attestation.py
sed -i 's/from datetime import datetime/from datetime import datetime, UTC/' roma_blackbox/attestation.py
sed -i 's/datetime.utcnow().isoformat() + "Z"/datetime.now(UTC).isoformat()/' roma_blackbox/attestation.py

# Fix 3: Update datetime in wrapper.py  
sed -i 's/from datetime import datetime/from datetime import datetime, UTC/' roma_blackbox/wrapper.py
sed -i 's/datetime.utcnow().isoformat()/datetime.now(UTC).isoformat()/g' roma_blackbox/wrapper.py

# Fix 4: Auto-fix ruff issues
ruff check --fix .

echo "✅ All fixes applied!"
