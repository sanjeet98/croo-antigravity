import os
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add src to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.identity import (
    load_credentials_and_derive_key,
    MissingCredentialError,
    InvalidKeyError
)

class TestIdentityInitialization(unittest.TestCase):

    def setUp(self):
        # Save a copy of the original environment
        self.original_env = dict(os.environ)
        # Clear target env vars
        for key in ["CROO_PRIVATE_KEY", "CROO_SDK_KEY", "CROO_BASE_URL", "CROO_WS_URL", "CROO_RPC_URL"]:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_missing_credentials_raises_error(self):
        # No env vars set
        with self.assertRaises(MissingCredentialError) as context:
            load_credentials_and_derive_key()
        
        self.assertIn("Systemic configuration dependencies missing", str(context.exception))
        self.assertIn("CROO_PRIVATE_KEY", str(context.exception))

    def test_invalid_key_raises_error(self):
        # Set all except valid private key
        os.environ["CROO_PRIVATE_KEY"] = "not-a-hex-string"
        os.environ["CROO_SDK_KEY"] = "test-sdk-key"
        os.environ["CROO_BASE_URL"] = "http://localhost:8000"
        os.environ["CROO_WS_URL"] = "ws://localhost:8000"

        with self.assertRaises(InvalidKeyError) as context:
            load_credentials_and_derive_key()
            
        self.assertIn("Failed to derive public key", str(context.exception))

    def test_successful_key_derivation(self):
        # 32-byte hex string private key
        valid_private_key = "01" * 32
        os.environ["CROO_PRIVATE_KEY"] = valid_private_key
        os.environ["CROO_SDK_KEY"] = "test-sdk-key"
        os.environ["CROO_BASE_URL"] = "http://localhost:8000"
        os.environ["CROO_WS_URL"] = "ws://localhost:8000"

        result = load_credentials_and_derive_key()
        
        self.assertEqual(result["private_key_hex"], valid_private_key)
        self.assertEqual(result["sdk_key"], "test-sdk-key")
        self.assertEqual(result["base_url"], "http://localhost:8000")
        self.assertEqual(result["ws_url"], "ws://localhost:8000")
        
        # Verify derived public key length (uncompressed ec point is 65 bytes = 130 hex characters starting with '04')
        self.assertTrue(result["public_key_hex"].startswith("04"))
        self.assertEqual(len(result["public_key_hex"]), 130)

if __name__ == "__main__":
    unittest.main()
