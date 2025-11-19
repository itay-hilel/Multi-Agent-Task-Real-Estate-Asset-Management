
import google.genai
import inspect
import pkgutil

print("Google GenAI package details:")
print(f"File: {google.genai.__file__}")
print(f"Dir: {dir(google.genai)}")

# Check if there are submodules
package = google.genai
for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
    print(f"Found submodule: {modname} (is_pkg={ispkg})")

# Inspect Client more closely
from google import genai
client = genai.Client(api_key="test")
print("\nClient attributes:")
for attr in dir(client):
    if not attr.startswith("_"):
        print(f"- {attr}")
        val = getattr(client, attr)
        print(f"  Type: {type(val)}")

