
import google.genai
from google import genai

client = genai.Client(api_key="test")

print("\nFiles attributes:")
for attr in dir(client.files):
    if not attr.startswith("_"):
        print(f"- {attr}")

print("\nChecking types for Corpus:")
import google.genai.types as types
for attr in dir(types):
    if "Corpus" in attr or "Retriever" in attr:
        print(f"- {attr}")

print("\nChecking if google.generativeai is installed:")
try:
    import google.generativeai as old_genai
    print(f"google.generativeai version: {old_genai.__version__}")
except ImportError:
    print("google.generativeai not installed")
