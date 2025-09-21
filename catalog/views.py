from rest_framework import viewsets , mixins , status 
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import F
from rest_framework.response import Response

from rest_framework.filters import SearchFilter , OrderingFilter 
from rest_framework.permissions import IsAuthenticated, AllowAny 
from django.db.models import Prefetch 

from .models import Category, Product, ProductVariant, Cart, CartItem
from .serializers import (CategorySerializer, ProductSerializer, CartSerializer,
                        CartItemSerializer, AddCartItemSerializer, UpdateCartItemSerializer)



class CategoryViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Category.objects.filter(parent_category=None).prefetch_related('subcategories')
    serializer_class = CategorySerializer
    permission_classes =[AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    filter_backends = [DjangoFilterBackend, SearchFilter , OrderingFilter]
    
    filterset_fields = {
        'category__slug': ['exact'],
        'variants__price': ['gte', 'lte'] # Filter by price range
    }
    search_fields = ['product_name', 'description']
    ordering_fields = ['variants__price', 'created_at']

    def get_queryset(self):
        queryset = Product.objects.filter(is_active = True)

        return queryset.select_related('category').prefetch_related(
            Prefetch('variants', queryset=ProductVariant.objects.order_by('price')), 'product_images'
            )
    
class CartViewSet(mixins.RetrieveModelMixin,mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.prefetch_related('items__variant__product').filter(user=self.request.user)

    def get_object(self):
        cart , _ = Cart.objects.get_or_create(user=self.request.user)
        return cart 
    
    def destroy(self, request, *args, **kwargs):
        cart = self.get_object()
        with transaction.atomic():
            # Restore stock for each cart item
            for item in cart.items.select_for_update().all():
                ProductVariant.objects.filter(pk=item.variant_id).update(
                    stock_quantity=F('stock_quantity') + item.quantity
                )
            # delete items
            cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemViewSet(mixins.CreateModelMixin,mixins.DestroyModelMixin, mixins.UpdateModelMixin , viewsets.GenericViewSet):
    http_method_names = ['post','patch','delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return AddCartItemSerializer 
        elif self.action == 'partial_update':
            return UpdateCartItemSerializer 
        return CartItemSerializer
    
    def get_serializer_context(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return {'cart_id': cart.id, 'user': self.request.user}

    def perform_destroy(self, instance):
       
        with transaction.atomic():
            # restore stock
            ProductVariant.objects.filter(pk=instance.variant_id).update(
                stock_quantity=F('stock_quantity') + instance.quantity
            )
            # then delete
            instance.delete()

        
    
