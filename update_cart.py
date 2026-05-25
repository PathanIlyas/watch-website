import re

def update_cart_template():
    with open('template/cart.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace hardcoded cart items with Django template loop
    cart_items_pattern = r'<!-- Cart Item 1 -->.*?<!-- Cart Item 2 -->.*?</div>\s*</div>\s*<div class="d-flex'
    
    dynamic_items = r'''
                    {% for item in items %}
                    <div class="row align-items-center cart-item mb-3">
                        <div class="col-12 col-md-6 d-flex align-items-center mb-3 mb-md-0">
                            <a href="{% url 'remove_from_cart' item.id %}" class="text-secondary me-3"><i class="fas fa-times"></i></a>
                            <img src="{% if item.watch.images.first %}{{ item.watch.images.first.image.url }}{% else %}{% static 'images/default_watch.png' %}{% endif %}" alt="{{ item.watch.name }}" class="cart-img me-3">
                            <div>
                                <a href="{% url 'product' item.watch.slug %}" class="text-white text-decoration-none fw-bold">{{ item.watch.name }}</a>
                                <p class="mb-0 text-secondary" style="font-size: 0.8rem;">Category: {{ item.watch.category.name }}</p>
                            </div>
                        </div>
                        <div class="col-4 col-md-2 text-center">
                            <span class="d-md-none text-secondary d-block" style="font-size: 0.8rem;">Price</span>
                            <span class="text-gold">${{ item.watch.price }}</span>
                        </div>
                        <div class="col-4 col-md-2 d-flex justify-content-center">
                            <span class="d-md-none text-secondary d-block mb-1" style="font-size: 0.8rem;">Qty</span>
                            <form method="post" action="{% url 'update_cart' item.id %}">
                                {% csrf_token %}
                                <div class="input-group input-group-sm" style="width: 90px;">
                                    <button class="btn btn-outline-secondary text-white rounded-0" type="submit" name="quantity" value="{{ item.quantity|add:'-1' }}">-</button>
                                    <input type="text" class="form-control text-center bg-transparent text-white border-secondary rounded-0 p-0" value="{{ item.quantity }}" readonly>
                                    <button class="btn btn-outline-secondary text-white rounded-0" type="submit" name="quantity" value="{{ item.quantity|add:'1' }}">+</button>
                                </div>
                            </form>
                        </div>
                        <div class="col-4 col-md-2 text-end fw-bold">
                            <span class="d-md-none text-secondary d-block" style="font-size: 0.8rem;">Total</span>
                            <span class="text-white">${% widthratio item.watch.price 1 item.quantity %}</span>
                        </div>
                    </div>
                    {% empty %}
                    <div class="text-center py-5">
                        <i class="fas fa-shopping-cart fa-3x text-secondary mb-3"></i>
                        <h4 class="text-white">Your cart is empty</h4>
                        <p class="text-secondary">Looks like you haven't added any luxury timepieces yet.</p>
                        <a href="{% url 'collection' %}" class="btn btn-gold mt-2">Browse Collection</a>
                    </div>
                    {% endfor %}

                    <div class="d-flex
'''
    html = re.sub(cart_items_pattern, dynamic_items, html, flags=re.DOTALL)
    
    # Update Order Summary
    summary_pattern = r'<div class="order-summary">.*?</div>\s*</div>'
    dynamic_summary = r'''<div class="order-summary">
                        <h4 class="text-white mb-4">Order Summary</h4>
                        <div class="d-flex justify-content-between mb-3">
                            <span class="text-secondary">Subtotal</span>
                            <span class="text-white fw-bold">${{ total }}</span>
                        </div>
                        <div class="d-flex justify-content-between mb-3 pb-3 border-bottom border-secondary">
                            <span class="text-secondary">Shipping</span>
                            <span class="text-white">Complimentary</span>
                        </div>
                        <div class="d-flex justify-content-between mb-4 mt-2">
                            <span class="text-white fs-5">Total</span>
                            <span class="text-gold fs-5 fw-bold">${{ total }}</span>
                        </div>
                        {% if items %}
                        <a href="{% url 'checkout' %}" class="btn btn-gold w-100 mb-3">Proceed To Checkout</a>
                        {% endif %}
                        <p class="text-center text-secondary mb-0" style="font-size: 0.8rem;"><i class="fas fa-lock me-1 text-gold"></i> Secure Checkout</p>
                    </div>
                </div>'''
    html = re.sub(summary_pattern, dynamic_summary, html, flags=re.DOTALL)

    with open('template/cart.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated cart.html")

if __name__ == '__main__':
    update_cart_template()
