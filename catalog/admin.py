from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Cart, CartItem

# Allows editing images directly on the Product admin page.
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1 # Show one extra empty form for adding a new image.
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        from django.utils.html import mark_safe
        return mark_safe(f'<img src="{obj.image.url}" width="150" height="auto" />')

# Allows editing variants directly on the Product admin page.
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category')
    search_fields = ('name',)
    # Automatically creates the 'slug' from the 'name' field.
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('product_name', 'description')
    prepopulated_fields = {'slug': ('product_name',)}
    # Include the inlines defined above.
    inlines = [ProductImageInline, ProductVariantInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'color', 'price', 'stock_quantity')
    list_filter = ('product__category',)
    search_fields = ('product__product_name',)
    # Makes it easier to edit price and stock quickly.
    list_editable = ('price', 'stock_quantity',)

# Basic admin views for Cart models
admin.site.register(Cart)
admin.site.register(CartItem)