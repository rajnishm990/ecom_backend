from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'cart/items', views.CartItemViewSet, basename='cart-item')


urlpatterns = [
    path('', include(router.urls)),
    path('cart/', views.CartViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='cart-detail'),
]

