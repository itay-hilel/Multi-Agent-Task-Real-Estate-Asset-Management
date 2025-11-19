"""
One-time setup script to create and populate Google File Search store
This store will be used for RAG queries about system documentation and data structure
"""

import os
import time
from google import genai
from dotenv import load_dotenv
import json

load_dotenv()

def create_file_search_store():
    """
    Creates a File Search store and uploads relevant documents.
    
    Returns:
        store_name (str): The name of the created store to be saved in config
    """
    
    # Initialize client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    client = genai.Client(api_key=api_key)
    
    print("📦 Creating File Search corpus...")
    # Use corpora (the actual API method name)
    corpus = client.corpora.create(display_name="Real Estate Knowledge Base")
    print(f"✅ Corpus created: {corpus.name}")
    
    # List of files to upload
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    files_to_upload = [
        {
            'path': os.path.join(parent_dir, "AI Developer Agent Real Estate Task.pdf"),
            'description': 'Task specification document'
        },
        {
            'path': os.path.join(current_dir, "data_dictionary.md"),
            'description': 'Generated data dictionary from cortex.parquet'
        }
    ]
    
    # Upload files to corpus
    uploaded_files = []
    for file_info in files_to_upload:
        file_path = file_info['path']
        
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            if 'data_dictionary.md' in file_path:
                print("   → Run generate_data_dictionary.py first!")
            continue
        
        print(f"\n📤 Uploading: {os.path.basename(file_path)}")
        print(f"   Description: {file_info['description']}")
        
        try:
            # Upload file to corpus
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            document = client.files.upload(
                path=file_path
            )
            
            # Create document in corpus
            client.corpora.documents.create(
                corpus=corpus.name,
                document=types.Document(
                    display_name=os.path.basename(file_path),
                    file=document
                )
            )
            
            print(f"   ✅ Upload complete: {os.path.basename(file_path)}")
            uploaded_files.append(os.path.basename(file_path))
            
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Save corpus configuration
    config = {
        'corpus_name': corpus.name,
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'uploaded_files': uploaded_files
    }
    
    config_path = os.path.join(current_dir, 'file_search_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to: {config_path}")
    print(f"\n📊 Summary:")
    print(f"   Corpus Name: {corpus.name}")
    print(f"   Files Uploaded: {len(uploaded_files)}")
    print(f"   Files: {', '.join(uploaded_files)}")
    
    print("\n🎯 Next Steps:")
    print("   1. The agent.py will automatically use this corpus")
    print("   2. Test with queries like:")
    print("      - 'What does ledger_category mean?'")
    print("      - 'Explain entity-level expenses'")
    print("      - 'What properties do we manage?'")
    
    return corpus.name

def list_existing_corpora():
    """List all existing corpora (for debugging)"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found")
    
    client = genai.Client(api_key=api_key)
    
    print("\n📚 Existing Corpora:")
    try:
        corpora = client.corpora.list()
        for idx, corpus in enumerate(corpora, 1):
            print(f"   {idx}. {corpus.name} - {corpus.display_name}")
    except Exception as e:
        print(f"   Error listing corpora: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  GOOGLE FILE SEARCH STORE SETUP")
    print("=" * 60)
    
    # First, check if data dictionary exists
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = os.path.join(current_dir, "data_dictionary.md")
    
    if not os.path.exists(dict_path):
        print("\n⚠️  data_dictionary.md not found!")
        print("   Run generate_data_dictionary.py first:")
        print("   $ python3 real_estate_agent/generate_data_dictionary.py")
        exit(1)
    
    # Create and populate corpus
    corpus_name = create_file_search_store()
    
    print("\n" + "=" * 60)
    print("  SETUP COMPLETE!")
    print("=" * 60)

