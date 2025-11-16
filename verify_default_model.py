"""Verify that Kimi K2 is now the default model"""

from backend.config import config
from backend.llm.chutes_client import ChutesClient
from backend.llm.model_router import ModelRouter

print("\n" + "=" * 80)
print("DEFAULT MODEL VERIFICATION")
print("=" * 80)

# Check config
print(f"\n1. Config Default Model:")
print(f"   {config.llm.default_model}")

# Check ChutesClient default
client = ChutesClient()
print(f"\n2. ChutesClient Default Model:")
print(f"   {client.default_model}")

# Check ModelRouter configuration
router = ModelRouter()
print(f"\n3. ModelRouter Available Models:")
for model in router.AVAILABLE_CLOUD_MODELS:
    status = "✓ RECOMMENDED" if model["recommended"] else "  "
    default_marker = " (DEFAULT)" if "(Default)" in model["name"] else ""
    print(f"   {status} {model['name']}{default_marker}")
    print(f"      ID: {model['id']}")
    print(f"      Description: {model['description'][:80]}...")
    print()

# Verify they all match
expected_model = "moonshotai/Kimi-K2-Thinking"
config_matches = config.llm.default_model == expected_model
client_matches = client.default_model == expected_model
router_recommends = router.AVAILABLE_CLOUD_MODELS[0]["id"] == expected_model

print("=" * 80)
print("VERIFICATION RESULTS")
print("=" * 80)

all_pass = config_matches and client_matches and router_recommends

if all_pass:
    print("\n✅ ALL CHECKS PASSED!")
    print(f"   Default model is correctly set to: {expected_model}")
    print(f"   - Config: ✓")
    print(f"   - ChutesClient: ✓")
    print(f"   - ModelRouter: ✓")
    print("\n🚀 Kimi K2 Thinking is now the default lesson generation model!")
else:
    print("\n❌ VERIFICATION FAILED!")
    if not config_matches:
        print(
            f"   - Config: ✗ (expected {expected_model}, got {config.llm.default_model})"
        )
    if not client_matches:
        print(
            f"   - ChutesClient: ✗ (expected {expected_model}, got {client.default_model})"
        )
    if not router_recommends:
        print(
            f"   - ModelRouter: ✗ (first model is {router.AVAILABLE_CLOUD_MODELS[0]['id']})"
        )

print("=" * 80 + "\n")
