import re

def update_collection_template():
    with open('template/collection.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Find the Product Grid section
    grid_pattern = r'<!-- Product Grid -->\s*<div class="row g-4">.*?</div>\s*<!-- Pagination -->'
    
    dynamic_grid = r'''<!-- Product Grid -->
            <div class="row g-4">
                {% for watch in watches %}
                <div class="col-lg-4 col-md-6" data-aos="fade-up" data-aos-delay="100">
                    <div class="watch-card text-center p-3">
                        <div class="watch-img-wrap">
                            <img src="{% if watch.images.first %}{{ watch.images.first.image.url }}{% else %}{% static 'images/default_watch.png' %}{% endif %}" alt="{{ watch.name }}">
                        </div>
                        <div class="watch-info">
                            <h3 class="watch-title text-white">{{ watch.name }}</h3>
                            <div class="watch-price">${{ watch.price }}</div>
                            <a href="{% url 'product' watch.slug %}" class="btn btn-outline-gold w-100">View Details</a>
                        </div>
                    </div>
                </div>
                {% empty %}
                <div class="col-12 text-center text-white py-5">
                    <h3>No watches available in the collection right now.</h3>
                </div>
                {% endfor %}
            </div>

            <!-- Pagination -->'''
    html = re.sub(grid_pattern, dynamic_grid, html, flags=re.DOTALL)

    with open('template/collection.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated collection.html")

if __name__ == '__main__':
    update_collection_template()
