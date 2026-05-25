import os
import re

dir_path = r'd:\watch-website'
html_files = [f for f in os.listdir(dir_path) if f.endswith('.html')]

for file in html_files:
    file_path = os.path.join(dir_path, file)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('href="index.html"', 'href="{% url \'home\' %}"')
    content = content.replace('href="collection.html"', 'href="{% url \'collection\' %}"')
    content = content.replace('href="about.html"', 'href="{% url \'about\' %}"')
    content = content.replace('href="contact.html"', 'href="{% url \'contact\' %}"')
    content = content.replace('href="cart.html"', 'href="{% url \'cart\' %}"')
    content = content.replace('href="checkout.html"', 'href="{% url \'checkout\' %}"')
    # Replace product.html but it requires a slug, for dummy put something
    content = content.replace('href="product.html"', 'href="{% url \'product\' \'sample-watch\' %}"')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
print('Done fixing URL tags')
