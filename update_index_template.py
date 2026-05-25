import re

def main():
    with open('template/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace trending slider
    html = re.sub(r'<div class="swiper-wrapper">.*?</div>\s*<div class="swiper-pagination', r'''<div class="swiper-wrapper">
                    {% for watch in trending_watches %}
                    <div class="swiper-slide">
                        <div class="watch-card text-center p-3">
                            <div class="watch-img-wrap">
                                <img src="{% if watch.images.first %}{{ watch.images.first.image.url }}{% else %}{% static 'images/default_watch.png' %}{% endif %}" alt="{{ watch.name }}">
                            </div>
                            <div class="watch-info">
                                <h3 class="watch-title text-white">{{ watch.name }}</h3>
                                <div class="watch-price">${{ watch.price }}</div>
                                <a href="{% url 'product' watch.slug %}" class="btn btn-outline-gold w-100">Quick View</a>
                            </div>
                        </div>
                    </div>
                    {% empty %}
                    <p class="text-white text-center">No trending watches available at the moment.</p>
                    {% endfor %}
                </div>
                <div class="swiper-pagination''', html, flags=re.DOTALL)

    # Replace Featured Collections Section
    html = re.sub(r'<div class="row g-4">(.*?)</div>\s*</div>\s*</section>\s*<!-- Trending', r'''<div class="row g-4">
                {% for watch in featured_watches %}
                <div class="col-md-3" data-aos="fade-up" data-aos-delay="100">
                    <a href="{% url 'product' watch.slug %}" class="text-decoration-none">
                        <div class="watch-card">
                            <div class="watch-img-wrap">
                                <img src="{% if watch.images.first %}{{ watch.images.first.image.url }}{% else %}{% static 'images/default_watch.png' %}{% endif %}" alt="{{ watch.name }}">
                            </div>
                            <div class="watch-info">
                                <h3 class="watch-title text-white">{{ watch.name }}</h3>
                                <p class="mb-0 text-gold">View Product</p>
                            </div>
                        </div>
                    </a>
                </div>
                {% empty %}
                <p class="text-white text-center">No featured watches at the moment.</p>
                {% endfor %}
            </div>
        </div>
    </section>
    <!-- Trending''', html, flags=re.DOTALL)
    
    with open('template/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print('Done index.html')

if __name__ == '__main__':
    main()
