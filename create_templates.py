import os

# تعريف التطبيقات والصفحات
apps = {
    "accounting_app": ["accounting/home.html"],
    "inventory": ["inventory/home.html"],
    "manufacturing_app": ["manufacturing/home.html"]
}

# محتوى HTML لكل صفحة (مبسط)
html_templates = {
    "accounting/home.html": """{% extends "base.html" %}
{% block title %}المحاسبة{% endblock %}
{% block content %}
<h2>قسم المحاسبة</h2>
<p>هنا يتم إدارة الحسابات والفواتير.</p>
{% endblock %}""",
    
    "inventory/home.html": """{% extends "base.html" %}
{% block title %}المستودعات{% endblock %}
{% block content %}
<h2>قسم المستودعات</h2>
<p>هنا يتم إدارة المخزون والمستودعات.</p>
{% endblock %}""",
    
    "manufacturing/home.html": """{% extends "base.html" %}
{% block title %}التصنيع{% endblock %}
{% block content %}
<h2>قسم التصنيع</h2>
<p>هنا يتم إدارة عمليات الإنتاج والتصنيع.</p>
{% endblock %}"""
}

# إنشاء المجلدات والملفات
for app, files in apps.items():
    for file in files:
        folder_path = os.path.join(app, "templates", os.path.dirname(file))
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, os.path.basename(file))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_templates[file])

print("تم إنشاء مجلدات Templates والملفات لكل التطبيقات بنجاح!")
