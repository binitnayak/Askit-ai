import os
import re

files_to_fix = [
    r'core/summarize.py',
    r'core/extractor.py',
    r'core/transcriber.py',
    r'core/rag_engine.py'
]

emojis = ['🧠', '📚', '📝', '🔗', '🔄', '✅', '⚠️', '❌', '⏭️', '🎙️', '📥', '📌', '📋', '🔑', '❓']

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all print statements and strip emojis from them
    def replacer(match):
        text = match.group(0)
        for e in emojis:
            text = text.replace(e, '')
        return text

    # Regex to match print statements
    new_content = re.sub(r'print\((.*?)\)', replacer, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
print("Removed emojis from print statements successfully!")
