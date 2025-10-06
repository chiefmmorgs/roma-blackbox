"""Example: Enhanced PII detection and redaction"""

from roma_blackbox.pii_patterns import EnhancedPIIRedactor, PIIPattern


def main():
    print("=== Enhanced PII Detection Example ===\n")

    # Create redactor
    redactor = EnhancedPIIRedactor()

    # Example data with various PII types
    sensitive_data = {
        "user": {
            "name": "John Doe",
            "email": "john.doe@company.com",
            "ssn": "123-45-6789",
            "phone": "(555) 123-4567",
            "credit_card": "4532-1488-0343-6467",
        },
        "system": {
            "ip_address": "192.168.1.100",
            "api_key": "sk_test_FAKE_KEY_FOR_TESTING_ONLY_12345",
            "aws_key": "AKIAIOSFODNN7EXAMPLE",
        },
        "crypto": {
            "btc": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "eth": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
        },
        "notes": "Contact user at john.doe@company.com or call 555-123-4567",
    }

    print("1. Original data (CONTAINS SENSITIVE INFO):")
    print("  user.email:", sensitive_data["user"]["email"])
    print("  user.ssn:", sensitive_data["user"]["ssn"])
    print("  system.api_key:", sensitive_data["system"]["api_key"][:20] + "...")
    print()

    # Scan for PII types
    print("2. Scanning for PII types:")
    findings = redactor.scan(sensitive_data)
    for pii_type, details in findings.items():
        print(f"  - {pii_type}: {details[0]}")
    print()

    # Redact PII
    print("3. Redacted data:")
    redacted = redactor.redact(sensitive_data)
    print("  user.email:", redacted["user"]["email"])
    print("  user.ssn:", redacted["user"]["ssn"])
    print("  user.credit_card:", redacted["user"]["credit_card"])
    print("  system.api_key:", redacted["system"]["api_key"])
    print("  crypto.btc:", redacted["crypto"]["btc"])
    print("  notes:", redacted["notes"])
    print()

    # Custom pattern example
    print("4. Custom pattern (Employee IDs):")
    custom_pattern = PIIPattern("employee_id", r"\bEMP-\d{6}\b", "[EMPLOYEE_ID]")
    custom_redactor = EnhancedPIIRedactor(custom_patterns=[custom_pattern])

    text = "Employee EMP-123456 reported an issue with EMP-789012"
    redacted_text = custom_redactor.redact(text)
    print(f"  Original: {text}")
    print(f"  Redacted: {redacted_text}")


if __name__ == "__main__":
    main()
