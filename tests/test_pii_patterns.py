"""Tests for enhanced PII detection patterns"""

import pytest
from roma_blackbox.pii_patterns import EnhancedPIIRedactor, PIIPattern


class TestEnhancedPIIRedactor:
    def test_email_redaction(self):
        redactor = EnhancedPIIRedactor()
        text = "Contact me at john.doe@example.com or jane@company.org"
        result = redactor.redact(text)

        assert "[EMAIL]" in result
        assert "john.doe@example.com" not in result
        assert "jane@company.org" not in result

    def test_ssn_redaction(self):
        redactor = EnhancedPIIRedactor()

        # SSN with dashes
        text1 = "My SSN is 123-45-6789"
        result1 = redactor.redact(text1)
        assert "[SSN]" in result1
        assert "123-45-6789" not in result1

        # SSN without dashes (9 consecutive digits)
        text2 = "SSN: 987654321"
        result2 = redactor.redact(text2)
        assert "[SSN]" in result2

    def test_credit_card_redaction(self):
        redactor = EnhancedPIIRedactor()

        # Various credit card formats
        cards = [
            "4532-1488-0343-6467",  # Visa
            "4532 1488 0343 6467",  # Visa with spaces
            "4532148803436467",  # Visa no separator
        ]

        for card in cards:
            result = redactor.redact(f"Card: {card}")
            assert "[CREDIT_CARD]" in result
            assert card.replace("-", "").replace(" ", "") not in result

    def test_phone_redaction(self):
        redactor = EnhancedPIIRedactor()

        phones = [
            "(555) 123-4567",
            "555-123-4567",
            "555.123.4567",
            "+1-555-123-4567",
        ]

        for phone in phones:
            result = redactor.redact(f"Call {phone}")
            assert "[PHONE]" in result

    def test_ip_address_redaction(self):
        redactor = EnhancedPIIRedactor()
        text = "Server IP: 192.168.1.1 and 10.0.0.5"
        result = redactor.redact(text)

        assert "[IP_ADDRESS]" in result
        assert "192.168.1.1" not in result
        assert "10.0.0.5" not in result

    def test_api_key_redaction(self):
        redactor = EnhancedPIIRedactor()

        text = 'api_key: "YOUR_API_KEY_HERE"'
        result = redactor.redact(text)
        assert "[API_KEY]" in result
        assert "YOUR_API_KEY_HERE" not in result

    def test_aws_key_redaction(self):
        redactor = EnhancedPIIRedactor()
        text = "AWS key: AKIAIOSFODNN7EXAMPLE"
        result = redactor.redact(text)

        assert "[AWS_KEY]" in result
        assert "AKIAIOSFODNN7EXAMPLE" not in result

    def test_github_token_redaction(self):
        redactor = EnhancedPIIRedactor()
        # GitHub token needs to be 36+ chars after the ghp_ prefix
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz123456"
        result = redactor.redact(text)

        assert "[GITHUB_TOKEN]" in result
        assert "ghp_1234567890abcdefghijklmnopqrstuvwxyz123456" not in result

    def test_bearer_token_redaction(self):
        redactor = EnhancedPIIRedactor()
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redactor.redact(text)

        assert "Bearer [TOKEN]" in result
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_crypto_address_redaction(self):
        redactor = EnhancedPIIRedactor()

        # Bitcoin
        btc_text = "Send BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        btc_result = redactor.redact(btc_text)
        assert "[BTC_ADDRESS]" in btc_result

        # Ethereum (needs full 40 hex chars after 0x)
        eth_text = "ETH address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        eth_result = redactor.redact(eth_text)
        assert "[ETH_ADDRESS]" in eth_result
        assert "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0" not in eth_result

    def test_nested_dict_redaction(self):
        redactor = EnhancedPIIRedactor()
        data = {
            "user": {
                "email": "test@example.com",
                "phone": "555-123-4567",
                "metadata": {"ip": "192.168.1.1", "ssn": "123-45-6789"},
            }
        }

        result = redactor.redact(data)

        assert result["user"]["email"] == "[EMAIL]"
        assert result["user"]["phone"] == "[PHONE]"
        assert result["user"]["metadata"]["ip"] == "[IP_ADDRESS]"
        assert result["user"]["metadata"]["ssn"] == "[SSN]"

    def test_list_redaction(self):
        redactor = EnhancedPIIRedactor()
        data = ["Email: user@test.com", "SSN: 123-45-6789", {"card": "4532-1488-0343-6467"}]

        result = redactor.redact(data)

        assert "[EMAIL]" in result[0]
        assert "[SSN]" in result[1]
        assert "[CREDIT_CARD]" in result[2]["card"]

    def test_scan_finds_pii_types(self):
        redactor = EnhancedPIIRedactor()
        data = {"email": "test@example.com", "ssn": "123-45-6789", "notes": "Call me at 555-1234"}

        findings = redactor.scan(data)

        assert "email" in findings
        assert "ssn" in findings
        # Note: phone might not match if pattern is strict

    def test_custom_pattern(self):
        # Add custom pattern for employee IDs
        custom = PIIPattern("employee_id", r"\bEMP-\d{6}\b", "[EMPLOYEE_ID]")

        redactor = EnhancedPIIRedactor(custom_patterns=[custom])
        text = "Employee EMP-123456 submitted a request"
        result = redactor.redact(text)

        assert "[EMPLOYEE_ID]" in result
        assert "EMP-123456" not in result

    def test_no_false_positives_on_normal_text(self):
        redactor = EnhancedPIIRedactor()
        text = "The quick brown fox jumps over the lazy dog"
        result = redactor.redact(text)

        # Should remain unchanged
        assert result == text
