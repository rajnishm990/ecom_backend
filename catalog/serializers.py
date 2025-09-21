from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant, Cart, CartItem



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductVariantSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'color', 'price', 'stock_quantity']

#for showing everything in one request if need be 
class ProductSerializer(serializers.ModelSerializer):
    
    variants = ProductVariantSerializer(many=True, read_only=True)
    product_images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField() # Display category name instead of ID

    class Meta:
        model = Product
        fields = ['id', 'product_name', 'slug', 'description', 'category', 'product_images', 'variants']

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]

class CategorySerializer(serializers.ModelSerializer):

    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'subcategories']

#FOR CART 

class SimpleProductVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model  = ProductVariant
        fields = ['id', 'product_name', 'size', 'color', 'price'] 

class CartItemSerializer(serializers.ModelSerializer):
    variant = SimpleProductVariantSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.variant.price

    class Meta:
        model =  CartItem
        fields = ['id', 'variant', 'quantity', 'total_price']

# Serializer for viewing the entire cart
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField()

    def get_grand_total(self, cart: Cart):
        # Calculate the total price of all items in the cart
        return sum(item.quantity * item.variant.price for item in cart.items.all())

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'grand_total', 'created_at']


class AddCardItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField()

    def validate_variant_id(self, value):
        #if variant exists
        if not ProductVariant.objects.filter(pk = value).exists():
            raise serializers.ValidationError("There is no variant with the given ID.")
        return value

    def validate(self, data):
        #for stock levels 
        variant = ProductVariant.objects.get(pk = data['variant_id'])
        if data['quanity'] > variant.stock_quantity:
            raise serializers.ValidationError(f"Not enough stock for {variant}. Available: {variant.stock_quantity}")
        return data
    
    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        variant_id = self.context['variant_id']
        quantity = self.context['quantity']

        try:
            #if items already exissts , incrase the quanity of it 
            cart_item = CartItem.objects.get(cart_id = cart_id , variant_id=variant_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)
        
        return self.instance 

    class Meta:
        model = CartItem
        fields = ['id', 'variant_id', 'quantity']

# Serializer for updating item quantity in the cart
class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']

    def validate_quantity(self, value):
        # Check stock when updating quantity
        if value > self.instance.variant.stock_quantity:
            raise serializers.ValidationError(f"Not enough stock. Available: {self.instance.variant.stock_quantity}")
        return value



