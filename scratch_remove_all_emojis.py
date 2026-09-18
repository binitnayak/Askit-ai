import os
import re

directories = ['core', 'utils', '.']
files = [
    'core/summarize.py',
    'core/extractor.py',
    'core/transcriber.py',
    'core/rag_engine.py',
    'core/vector_store.py',
    'app.py'
]

for filepath in files:
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all print statements and remove emojis (non-ascii characters)
    def replacer(match):
        text = match.group(0)
        # Only keep ascii characters in the print string
        clean_text = ''.join(c for c in text if ord(c) < 128)
        return clean_text

    new_content = re.sub(r'print\((.*?)\)', replacer, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
print("Removed all non-ascii characters from print statements successfully!")
