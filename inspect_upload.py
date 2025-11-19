
import inspect
from google import genai
from google.genai import types

client = genai.Client(api_key="test")
print("Signature of client.files.upload:")
print(inspect.signature(client.files.upload))
