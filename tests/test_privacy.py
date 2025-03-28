from app.services.privacy import scrub_pii

def test_scrub_pii():
    # Sample text with various PII types
    text = "My name is John Doe, I live in New York, and my email is john.doe@example.com." # TODO: Add "My phone number is 555-1234" later.

    # Scrub the PII from the text
    redacted_text = scrub_pii(text)

    # Expected output
    expected_output = "My name is [REDACTED], I live in [REDACTED], and my email is [REDACTED]." # TODO: My phone number is [REDACTED].

    # Check if the scrubbed text matches the expected output
    assert redacted_text == expected_output, f"Expected: {expected_output}, but got: {redacted_text}"

    print("PII scrubbing test passed!")

# Run the test
test_scrub_pii()