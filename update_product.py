import re

def update_product_template():
    with open('template/product.html', 'r', encoding='utf-8') as f:
        html = f.read()

    html = re.sub(r'Chronos Aureus - Product Details', r'{{ watch.name }} - Product Details', html)
    html = re.sub(r'<li class="breadcrumb-item active text-white".*?</li>', r'<li class="breadcrumb-item active text-white" aria-current="page">{{ watch.name }}</li>', html)

    gallery_html = r'''
                <div class="col-lg-6" data-aos="fade-right">
                    <div class="product-gallery-img">
                        <img src="{% if watch.images.first %}{{ watch.images.first.image.url }}{% else %}{% static 'images/default_watch.png' %}{% endif %}" alt="{{ watch.name }}" class="img-fluid mouse-glow" style="cursor: zoom-in;" id="mainProductImage">
                    </div>
                    <div class="row g-3 mt-1">
                        {% for img in watch.images.all %}
                        <div class="col-4">
                            <div class="product-gallery-img p-3 {% if forloop.first %}border-gold{% endif %}" {% if forloop.first %}style="border-color: var(--accent-gold);"{% endif %} onclick="document.getElementById('mainProductImage').src='{{ img.image.url }}'">
                                <img src="{{ img.image.url }}" alt="Thumb" class="img-fluid">
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
'''
    html = re.sub(r'<div class="col-lg-6" data-aos="fade-right">.*?</div>\s*<!-- Product Info -->', gallery_html + '\n                <!-- Product Info -->', html, flags=re.DOTALL)

    info_html = r'''
                <div class="col-lg-6" data-aos="fade-left">
                    <h1 class="display-5 text-white mb-2">{{ watch.name }}</h1>
                    <p class="text-gold fs-4 font-heading fw-bold mb-4">${{ watch.price }}</p>
                    
                    <p class="mb-4">{{ watch.description }}</p>
                    
                    <div class="row mb-4">
                        <div class="col-12">
                            <p class="text-white mb-1"><strong>Features:</strong> {{ watch.features }}</p>
                            <p class="text-white mb-1"><strong>Stock:</strong> {% if watch.stock_quantity > 0 %}{{ watch.stock_quantity }} Available{% else %}Out of Stock{% endif %}</p>
                            <p class="text-white mb-1"><strong>Brand:</strong> {{ watch.brand }}</p>
                            <p class="text-white mb-1"><strong>Category:</strong> {{ watch.category.name }}</p>
                        </div>
                    </div>

                    <form method="post" action="{% url 'add_to_cart' watch.id %}">
                        {% csrf_token %}
                        <div class="d-flex gap-3 mb-5 mt-4">
                            <button type="submit" class="btn btn-gold flex-grow-1" {% if watch.stock_quantity <= 0 %}disabled{% endif %}>
                                {% if watch.stock_quantity > 0 %}Add To Cart{% else %}Out of Stock{% endif %}
                            </button>
                        </div>
                    </form>
'''
    html = re.sub(r'<div class="col-lg-6" data-aos="fade-left">.*?<div class="accordion accordion-flush', info_html + '\n                    <div class="accordion accordion-flush', html, flags=re.DOTALL)

    with open('template/product.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated product.html")

if __name__ == '__main__':
    update_product_template()
