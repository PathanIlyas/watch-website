import os
import glob
import re

def update_cart_badges():
    template_dir = 'template'
    html_files = glob.glob(os.path.join(template_dir, '*.html'))
    
    # Regex to find the cart span containing '2' or any hardcoded number
    # Original: <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-gold" style="background-color: var(--accent-gold); color: #000;">2</span>
    pattern = r'(<span[^>]*class="[^"]*badge[^"]*"[^>]*>)\s*\d+\s*(</span>)'
    replacement = r'\g<1>{{ cart_count|default:"0" }}\g<2>'

    for file_path in html_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file_path}")

if __name__ == '__main__':
    update_cart_badges()
