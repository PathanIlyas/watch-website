import os
import re

dir_path = r'd:\watch-website'
html_files = [f for f in os.listdir(dir_path) if f.endswith('.html')]

for file in html_files:
    file_path = os.path.join(dir_path, file)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '{% load static %}' not in content:
        content = '{% load static %}\n' + content

    def repl_css(m): return 'href="{% static \'' + 'css/' + m.group(1) + '\' %}"'
    def repl_js(m): return 'src="{% static \'' + 'js/' + m.group(1) + '\' %}"'
    def repl_img(m): return 'src="{% static \'' + 'images/' + m.group(1) + '\' %}"'
    def repl_bg(m): return 'url(\'{% static \'' + 'images/' + m.group(1) + '\' %}\')'

    content = re.sub(r'href="css/([^"]+)"', repl_css, content)
    content = re.sub(r'src="js/([^"]+)"', repl_js, content)
    content = re.sub(r'src="images/([^"]+)"', repl_img, content)
    content = re.sub(r"url\('images/([^']+)'\)", repl_bg, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
print('Done processing HTML files')
