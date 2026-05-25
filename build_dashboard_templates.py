import os

base_dir = "d:/watch-website/dashboard/templates/dashboard/"
os.makedirs(os.path.join(base_dir, "products"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "orders"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "users"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "categories"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "banners"), exist_ok=True)

templates = {
    "products/list.html": """{% extends 'dashboard/base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>Products</h2>
    <a href="{% url 'dashboard_product_create' %}" class="btn btn-outline-warning"><i class="fas fa-plus"></i> Add Product</a>
</div>
<div class="glass-card">
    <div class="table-responsive">
        <table class="table table-dark table-hover mb-0">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Brand</th>
                    <th>Price</th>
                    <th>Stock</th>
                    <th>Category</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for watch in watches %}
                <tr>
                    <td>{{ watch.name }}</td>
                    <td>{{ watch.brand }}</td>
                    <td>${{ watch.price }}</td>
                    <td>{{ watch.stock_quantity }}</td>
                    <td>{{ watch.category.name }}</td>
                    <td>
                        <a href="{% url 'dashboard_product_update' watch.pk %}" class="btn btn-sm btn-outline-info"><i class="fas fa-edit"></i></a>
                        <a href="{% url 'dashboard_product_delete' watch.pk %}" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}""",

    "products/form.html": """{% extends 'dashboard/base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>{{ title }}</h2>
    <a href="{% url 'dashboard_products' %}" class="btn btn-outline-light"><i class="fas fa-arrow-left"></i> Back</a>
</div>
<div class="glass-card">
    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        <div class="row">
            {% for field in form %}
            <div class="col-md-6 mb-3">
                <label class="form-label text-muted">{{ field.label }}</label>
                {{ field }}
                {% if field.errors %}
                <div class="text-danger mt-1"><small>{{ field.errors|striptags }}</small></div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        <div class="mt-4">
            <button type="submit" class="btn btn-warning px-4">Save Product</button>
        </div>
    </form>
</div>
{% endblock %}""",

    "orders/list.html": """{% extends 'dashboard/base.html' %}
{% block content %}
<div class="mb-4">
    <h2>Orders</h2>
</div>
<div class="glass-card">
    <div class="table-responsive">
        <table class="table table-dark table-hover mb-0">
            <thead>
                <tr>
                    <th>Order ID</th>
                    <th>Customer</th>
                    <th>Date</th>
                    <th>Total Amount</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for order in orders %}
                <tr>
                    <td>#{{ order.id }}</td>
                    <td>{{ order.first_name }} {{ order.last_name }}</td>
                    <td>{{ order.created_at|date:"M d, Y" }}</td>
                    <td>${{ order.total_amount }}</td>
                    <td>
                        <span class="badge {% if order.status == 'Delivered' %}badge-green{% elif order.status == 'Pending' %}badge-gold{% else %}badge-red{% endif %}">
                            {{ order.status }}
                        </span>
                    </td>
                    <td>
                        <a href="{% url 'dashboard_order_update' order.pk %}" class="btn btn-sm btn-outline-info">Update Status</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}""",

    "orders/form.html": """{% extends 'dashboard/base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>Update Order #{{ order.id }}</h2>
    <a href="{% url 'dashboard_orders' %}" class="btn btn-outline-light"><i class="fas fa-arrow-left"></i> Back</a>
</div>
<div class="row">
    <div class="col-md-6 mb-4">
        <div class="glass-card">
            <h4 class="mb-3">Customer Details</h4>
            <p><strong>Name:</strong> {{ order.first_name }} {{ order.last_name }}</p>
            <p><strong>Email:</strong> {{ order.email }}</p>
            <p><strong>Phone:</strong> {{ order.phone }}</p>
            <p><strong>Address:</strong> {{ order.address }}, {{ order.city }}, {{ order.country }}</p>
            <p><strong>Total Amount:</strong> ${{ order.total_amount }}</p>
        </div>
    </div>
    <div class="col-md-6 mb-4">
        <div class="glass-card">
            <h4 class="mb-3">Update Status</h4>
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label class="form-label text-muted">Order Status</label>
                    {{ form.status }}
                </div>
                <button type="submit" class="btn btn-warning">Update Order</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}""",

    "users/list.html": """{% extends 'dashboard/base.html' %}
{% block content %}
<div class="mb-4">
    <h2>Users</h2>
</div>
<div class="glass-card">
    <div class="table-responsive">
        <table class="table table-dark table-hover mb-0">
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Date Joined</th>
                    <th>Is Staff</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <td>{{ user.username }}</td>
                    <td>{{ user.email }}</td>
                    <td>{{ user.date_joined|date:"M d, Y" }}</td>
                    <td>
                        {% if user.is_staff %}<i class="fas fa-check text-success"></i>{% else %}<i class="fas fa-times text-danger"></i>{% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}""",

    "categories/list.html": """{% extends 'dashboard/base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>Categories</h2>
    <a href="{% url 'dashboard_category_create' %}" class="btn btn-outline-warning"><i class="fas fa-plus"></i> Add Category</a>
</div>
<div class="glass-card">
    <div class="table-responsive">
        <table class="table table-dark table-hover mb-0">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Slug</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for category in categories %}
                <tr>
                    <td>{{ category.name }}</td>
                    <td>{{ category.slug }}</td>
                    <td>
                        <a href="#" class="btn btn-sm btn-outline-info"><i class="fas fa-edit"></i></a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}""",

    "categories/form.html": """{% extends 'dashboard/base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>{{ title }}</h2>
    <a href="{% url 'dashboard_categories' %}" class="btn btn-outline-light"><i class="fas fa-arrow-left"></i> Back</a>
</div>
<div class="glass-card">
    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        <div class="row">
            {% for field in form %}
            <div class="col-md-6 mb-3">
                <label class="form-label text-muted">{{ field.label }}</label>
                {{ field }}
            </div>
            {% endfor %}
        </div>
        <div class="mt-4">
            <button type="submit" class="btn btn-warning px-4">Save Category</button>
        </div>
    </form>
</div>
{% endblock %}""",

    "banners/list.html": """{% extends 'dashboard/base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>Homepage Banners</h2>
    <a href="{% url 'dashboard_banner_create' %}" class="btn btn-outline-warning"><i class="fas fa-plus"></i> Add Banner</a>
</div>
<div class="glass-card">
    <div class="table-responsive">
        <table class="table table-dark table-hover mb-0">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Link</th>
                    <th>Active</th>
                </tr>
            </thead>
            <tbody>
                {% for banner in banners %}
                <tr>
                    <td>{{ banner.title }}</td>
                    <td>{{ banner.link }}</td>
                    <td>{% if banner.is_active %}<i class="fas fa-check text-success"></i>{% else %}<i class="fas fa-times text-danger"></i>{% endif %}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}""",

    "banners/form.html": """{% extends 'dashboard/base.html' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>{{ title }}</h2>
    <a href="{% url 'dashboard_banners' %}" class="btn btn-outline-light"><i class="fas fa-arrow-left"></i> Back</a>
</div>
<div class="glass-card">
    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        <div class="row">
            {% for field in form %}
            <div class="col-md-6 mb-3">
                <label class="form-label text-muted">{{ field.label }}</label>
                {{ field }}
            </div>
            {% endfor %}
        </div>
        <div class="mt-4">
            <button type="submit" class="btn btn-warning px-4">Save Banner</button>
        </div>
    </form>
</div>
{% endblock %}""",
}

for filepath, content in templates.items():
    with open(os.path.join(base_dir, filepath), 'w') as f:
        f.write(content)

print("Templates generated successfully.")
