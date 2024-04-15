print("""
To do:
    implement client website whitelist
    implement local database for storage
      implement live server test
""")
import secrets

def generate_random_string(length):
    """Generates a cryptographically strong random string of the specified length."""
    # Each byte has 2 hex digits, so we need length * 2 hex digits
    return secrets.token_hex(length)

def get_random_string():
    """Returns a random string of length 16, 24, or 32 bytes."""
    length = secrets.choice([16, 24, 32])  # Randomly choose between 16, 24, or 32 bytes
    return generate_random_string(length)

# Example usage
if __name__ == "__main__":
    random_string = get_random_string()
    print(f"Random String: {random_string}")
    print(f"Length of String in Bytes: {len(random_string)//2}")