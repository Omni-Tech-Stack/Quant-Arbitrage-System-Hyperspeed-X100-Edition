# bloXroute API Configuration
# This file contains the necessary credentials for interacting with the bloXroute BDN API.

# The authorization header is a Base64 encoding of your Account ID and a secret key.
# It is used to authenticate API requests.
BLOXROUTE_AUTH_HEADER = "MTU1MGZiYmEtNDdiNS00YzA3LTg4NTAtZGVjN2Q4YWU5MDY5OmVhMGVhZTJmZTMwMGRkYzJiN2M2MTczZDAwNDg5MDE3"

# bloXroute API endpoints
BLOXROUTE_BDN_API_URL = "https://api.blxrbdn.com"
BLOXROUTE_RELAY_API_URL = BLOXROUTE_BDN_API_URL  # Alias for backward compatibility with bloxroute_real_gateway imports
BLOXROUTE_SUBMIT_BUNDLE_ENDPOINT = f"{BLOXROUTE_BDN_API_URL}/api/v2/submit-bundle"
