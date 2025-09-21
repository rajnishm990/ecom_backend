from rest_framework import serializers
from django.db import transaction
from django.db.models import F
from .models import Category, Product, ProductImage, ProductVariant, Cart, CartItem




class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductVariantSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'color', 'price', 'stock_quantity']

#for showing everything in one request 
class ProductSerializer(serializers.ModelSerializer):
    
    variants = ProductVariantSerializer(many=True, read_only=True)
    product_images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField() # Display category name instead of ID (Note for self: Read Only field , switch to write_able if need be)

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

    product_name = serializers.CharField(source = 'product.product_name' , read_only =True)

    class Meta:
        model  = ProductVariant
        fields = ['id', 'product_name', 'size', 'color', 'price'] 

class CartItemSerializer(serializers.ModelSerializer):
    variant = SimpleProductVariantSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item: CartItem):

        if not cart_item.variant:
            return 0
        
        return cart_item.quantity * cart_item.variant.price

    class Meta:
        model =  CartItem
        fields = ['id', 'variant', 'quantity', 'total_price']

# Serializer for viewing the entire cart
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField()
    user = serializers.CharField(source='user.username', read_only=True) 

    def get_grand_total(self, cart: Cart):
        # Calculate the total price of all items in the cart
        items = cart.items.all()
        return sum((item.quantity * (item.variant.price if item.variant else 0)) for item in items)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'grand_total', 'created_at']


class AddCartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField()

    def validate_variant_id(self, value):
        #if variant exists
        if not ProductVariant.objects.filter(pk = value).exists():
            raise serializers.ValidationError("There is no variant with the given ID.")
        return value

    def validate(self, data):
        # Basic positive quantity enforced by IntegerField(min_value=1)
        return data
    
    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        variant_id = self.validated_data['variant_id']
        add_qty = self.validated_data['quantity']

        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().get(pk = variant_id)

            if variant.stock_quantity < add_qty:
                raise serializers.ValidationError(
                    f"Not enough stock for {variant}. Available: {variant.stock_quantity}"
                )
            #locking existing cart for presetn item
            cart_item = CartItem.objects.select_for_update().filter(cart_id=cart_id , variant_id=variant_id).first()

            if cart_item:
                new_qty = cart_item.quantity + add_qty
               
                #check against current 
                if variant.stock_quantity < add_qty:
                    # second check is redundant with earlier check but explicit.
                    raise serializers.ValidationError(
                        f"Not enough stock to add {add_qty}. Available: {variant.stock_quantity}"
                    )
               
                # update quantity
                cart_item.quantity = F('quantity') + add_qty
                cart_item.save()
                cart_item.refresh_from_db()
            
            else:
                cart_item = CartItem.objects.create(
                    cart_id=cart_id,
                    variant_id=variant_id,
                    quantity=add_qty
                )  
            # Decrement stock atomically
            
            ProductVariant.objects.filter(pk=variant_id).update(
                stock_quantity=F('stock_quantity') - add_qty
            )
            variant.refresh_from_db()

            self.instance = cart_item
            return self.instance         
        

    class Meta:
        model = CartItem
        fields = ['id', 'variant_id', 'quantity']

# Serializer for updating item quantity in the cart

class UpdateCartItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ['quantity']

    def validate_quantity(self, value):
        # If increasing quantity, ensure enough stock exists
        current_qty = self.instance.quantity
        if value > current_qty:
            # need extra units
            need = value - current_qty
            variant = ProductVariant.objects.filter(pk=self.instance.variant_id).first()
            if not variant:
                raise serializers.ValidationError("Variant no longer exists.")
            if variant.stock_quantity < need:
                raise serializers.ValidationError(f"Not enough stock. Available: {variant.stock_quantity}")
        return value

    def save(self, **kwargs):
        """
        Adjust stock depending on delta:
          - if quantity increased: decrement stock by delta
          - if decreased: increment stock by (-delta)
        All done inside a transaction with select_for_update on variant and cart_item.
        """
        new_qty = self.validated_data['quantity']
        cart_item = self.instance
        delta = new_qty - cart_item.quantity  # positive -> need more; negative -> release

        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().get(pk=cart_item.variant_id)

            if delta > 0:
                # trying to increase quantity
                if variant.stock_quantity < delta:
                    raise serializers.ValidationError(f"Not enough stock. Available: {variant.stock_quantity}")
                # decrement stock
                ProductVariant.objects.filter(pk=variant.pk).update(stock_quantity=F('stock_quantity') - delta)
            elif delta < 0:
                # releasing stock
                ProductVariant.objects.filter(pk=variant.pk).update(stock_quantity=F('stock_quantity') + (-delta))

            # update cart item quantity
            cart_item.quantity = new_qty
            cart_item.save()
            cart_item.refresh_from_db()

        return cart_item



