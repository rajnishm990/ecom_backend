from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Category(models.Model):

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, blank=True , null=True , related_name='subcategories')

    class Meta:
        verbose_name_plural = "Categories" 
        unique_together = ('name', 'parent_category')

    def __str__(self):
        # Shows the hierarchy in the admin panel for clarity.
        full_path = [self.name]
        k = self.parent_category
        while k is not None:
            full_path.append(k.name)
            k = k.parent_category
        return ' -> '.join(full_path[::-1])

class Product(models.Model):
    product_name = models.CharField(max_length=200)
    slug =  models.SlugField(max_length=250 , unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT , related_name='products')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =  models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name
    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product , on_delete=models.CASCADE ,related_name='variants')
    size = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10 , decimal_places=2 , validators=[MinValueValidator(0.01)])
    stock_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size', 'color') #ensuring can't have two variant of same product with same color and size
    
    def __str__(self):
        return f"{self.product.product_name} ({self.size}, {self.color})"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart , on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'variant')

    def __str__(self):
        return f"{self.quantity} of {self.variant}" 
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to='products/', help_text="Image for the product.")

    def __str__(self):
        return f"Image for {self.product.product_name}"



