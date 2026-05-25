import re

def update_checkout_template():
    with open('template/checkout.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Update form to have method="post" and add name attributes
    form_pattern = r'<form>.*?<button type="submit"'
    dynamic_form = r'''<form method="post" action="{% url 'checkout' %}">
                        {% csrf_token %}
                        <!-- Contact Information -->
                        <div class="mb-5">
                            <h4 class="text-white mb-4">Contact Information</h4>
                            <div class="mb-3">
                                <input type="email" name="email" class="form-control" placeholder="Email Address" required>
                            </div>
                        </div>

                        <!-- Shipping Address -->
                        <div class="mb-5">
                            <h4 class="text-white mb-4">Shipping Address</h4>
                            <div class="row g-3">
                                <div class="col-12">
                                    <select class="form-select" name="country" required>
                                        <option value="" selected disabled>Country/Region</option>
                                        <option value="US">United States</option>
                                        <option value="UK">United Kingdom</option>
                                        <option value="CH">Switzerland</option>
                                        <option value="AE">United Arab Emirates</option>
                                        <option value="IN">India</option>
                                    </select>
                                </div>
                                <div class="col-md-6">
                                    <input type="text" name="first_name" class="form-control" placeholder="First name" required>
                                </div>
                                <div class="col-md-6">
                                    <input type="text" name="last_name" class="form-control" placeholder="Last name" required>
                                </div>
                                <div class="col-12">
                                    <input type="text" name="address" class="form-control" placeholder="Address" required>
                                </div>
                                <div class="col-md-4">
                                    <input type="text" name="city" class="form-control" placeholder="City" required>
                                </div>
                                <div class="col-md-4">
                                    <input type="text" name="state" class="form-control" placeholder="State/Province" required>
                                </div>
                                <div class="col-md-4">
                                    <input type="text" name="postal_code" class="form-control" placeholder="ZIP/Postal code" required>
                                </div>
                                <div class="col-12">
                                    <input type="tel" name="phone" class="form-control" placeholder="Phone" required>
                                </div>
                            </div>
                        </div>
                        
                        <input type="hidden" name="payment_method" value="Credit Card">

                        <button type="submit"'''
    html = re.sub(form_pattern, dynamic_form, html, flags=re.DOTALL)

    # Update checkout summary
    summary_pattern = r'<div class="order-summary sticky-top".*?</section>'
    dynamic_summary = r'''<div class="order-summary sticky-top" style="top: 100px;">
                        <h4 class="text-white mb-4">In Your Bag</h4>
                        
                        {% for item in items %}
                        <div class="d-flex align-items-center mb-4 {% if forloop.last %}pb-4 border-bottom border-secondary{% endif %}">
                            <div class="position-relative me-3">
                                <img src="{% if item.watch.images.first %}{{ item.watch.images.first.image.url }}{% else %}{% static 'images/default_watch.png' %}{% endif %}" alt="{{ item.watch.name }}" class="cart-img" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;">
                                <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-secondary text-white">{{ item.quantity }}</span>
                            </div>
                            <div class="flex-grow-1">
                                <h6 class="text-white mb-0">{{ item.watch.name }}</h6>
                                <p class="text-secondary small mb-0">{{ item.watch.category.name }}</p>
                            </div>
                            <span class="text-white fw-bold">${% widthratio item.watch.price 1 item.quantity %}</span>
                        </div>
                        {% endfor %}

                        <div class="d-flex justify-content-between mb-2 text-secondary">
                            <span>Subtotal</span>
                            <span class="text-white">${{ total }}</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2 text-secondary">
                            <span>Shipping</span>
                            <span class="text-white">Complimentary</span>
                        </div>
                        <div class="d-flex justify-content-between mb-4 pb-4 border-bottom border-secondary text-secondary">
                            <span>Taxes (Estimated)</span>
                            <span class="text-white">$0.00</span>
                        </div>

                        <div class="d-flex justify-content-between align-items-center">
                            <span class="text-white fs-5">Total</span>
                            <div class="text-end">
                                <span class="text-secondary small me-2">USD</span>
                                <span class="text-gold fs-4 fw-bold">${{ total }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>'''
    html = re.sub(summary_pattern, dynamic_summary, html, flags=re.DOTALL)

    with open('template/checkout.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated checkout.html")

if __name__ == '__main__':
    update_checkout_template()
