"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from stationery.views import (
    AdminLoginView,
    view_products,
    view_product_by_id,
    add_product,
    edit_product,
    view_stock,
    view_imports,
    add_import,
    view_exports,
    add_export,
    report_view
)

urlpatterns = [
    # Utils view
    path("", view_products),
    # Authentication view
    path("login/", AdminLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Product view
    path("products/", view_products, name="view_products"),
    path("products/<int:id>/", view_product_by_id, name="view_product_by_id"),
    path("products/add/", add_product, name="add_product"),
    path("products/stocks/", view_stock, name="view_stock"),
    path("products/<int:id>/edit/", edit_product, name="edit_product"),
    path('imports/', view_imports, name='view_imports'),
    path('imports/add/', add_import, name='add_import'),
    path('exports/', view_exports, name='view_exports'),
    path('exports/add/', add_export, name='add_export'),
    # Report view
    path('report/', report_view, name='report_view'),
    # Admin view
    path("admin/", admin.site.urls),
    # Static files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]