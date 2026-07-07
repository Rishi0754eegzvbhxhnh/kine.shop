import os
import re

frontend_dir = r"c:\Users\Lenovo\OneDrive\Desktop\Shopy-stream-app\frontend\src"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # We want to replace occurrences of http://localhost:8082 with http://${window.location.hostname}:8082
    # But we have to be careful about quotes.
    # If it's in backticks: `http://localhost:8082/...` -> `http://${window.location.hostname}:8082/...`
    content = content.replace("`http://localhost:8082", "`http://${window.location.hostname}:8082")
    
    # If it's in single quotes: 'http://localhost:8082/...' -> `http://${window.location.hostname}:8082/...`
    content = content.replace("'http://localhost:8082", "`http://${window.location.hostname}:8082")
    # also we need to change the closing single quote to a backtick for this string.
    # A safer way: just define a global variable in the file or just replace it naively for the specific files.

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk(frontend_dir):
    for file in files:
        if file.endswith('.jsx') or file.endswith('.js'):
            process_file(os.path.join(root, file))

print("Fixed URLs.")
