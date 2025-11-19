"""
One-time setup script to upload documents for RAG (Long Context)
This script uploads documents to Google GenAI File API to be used by the agent.
"""

import os
import time
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

def setup_rag_files():
    """
    Uploads relevant documents to Google GenAI File API.
    
    Returns:
        config (dict): The configuration to be saved.
    """
    
    # Initialize client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    client = genai.Client(api_key=api_key)
    
    print("📦 Starting File Upload for RAG...")
    
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
    
    uploaded_files_info = []
    
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
            # Upload file
            # Note: client.files.upload returns a File object with .uri attribute
            upload_config = None
            if file_path.endswith('.md'):
                upload_config = {'mime_type': 'text/markdown'}
            
            file_obj = client.files.upload(file=file_path, config=upload_config)
            
            print(f"   ✅ Upload complete: {file_obj.name}")
            print(f"   🔗 URI: {file_obj.uri}")
            
            uploaded_files_info.append({
                'name': file_obj.name,
                'uri': file_obj.uri,
                'display_name': os.path.basename(file_path),
                'mime_type': file_obj.mime_type
            })
            
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Save configuration
    config = {
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'uploaded_files': uploaded_files_info,
        # For backward compatibility with single-file agent (will use the last one if multiple)
        'file_uri': uploaded_files_info[-1]['uri'] if uploaded_files_info else None,
        'file_name': uploaded_files_info[-1]['display_name'] if uploaded_files_info else None
    }
    
    config_path = os.path.join(current_dir, 'file_search_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to: {config_path}")
    print(f"\n📊 Summary:")
    print(f"   Files Uploaded: {len(uploaded_files_info)}")
    for f in uploaded_files_info:
        print(f"   - {f['display_name']} ({f['uri']})")
    
    print("\n🎯 Next Steps:")
    print("   1. The agent.py will automatically use these files")
    
    return config

if __name__ == "__main__":
    print("=" * 60)
    print("  GOOGLE GENAI FILE SETUP")
    print("=" * 60)
    
    # First, check if data dictionary exists
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = os.path.join(current_dir, "data_dictionary.md")
    
    if not os.path.exists(dict_path):
        print("\n⚠️  data_dictionary.md not found!")
        print("   Run generate_data_dictionary.py first:")
        print("   $ python3 real_estate_agent/generate_data_dictionary.py")
        exit(1)
    
    # Run setup
    setup_rag_files()
    
    print("\n" + "=" * 60)
    print("  SETUP COMPLETE!")
    print("=" * 60)

