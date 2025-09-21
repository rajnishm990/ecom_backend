import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from catalog.models import Category, Product, ProductVariant

class Command(BaseCommand):
    help = 'Seeds the database with initial data for categories, products, and a superuser.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        # --- Clean Slate ---
        User.objects.all().delete()
        Category.objects.all().delete()
        Product.objects.all().delete()

        # --- Create Superuser ---
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        self.stdout.write(self.style.SUCCESS('Admin user created (admin/admin123).'))

        # --- Create Categories ---
        clothing = Category.objects.create(name='Clothing', slug='clothing')
        men = Category.objects.create(name='Men', slug='men', parent_category=clothing)
        women = Category.objects.create(name='Women', slug='women', parent_category=clothing)
        t_shirts_men = Category.objects.create(name='T-Shirts', slug='t-shirts-men', parent_category=men)
        t_shirts_women = Category.objects.create(name='T-Shirts', slug='t-shirts-women', parent_category=women)

        electronics = Category.objects.create(name='Electronics', slug='electronics')
        phones = Category.objects.create(name='Smartphones', slug='smartphones', parent_category=electronics)
        self.stdout.write(self.style.SUCCESS('Categories created.'))

        # --- Create Products & Variants ---
        products_data = [
            {
                'category': t_shirts_men,
                'name': 'Classic Cotton Crewneck T-Shirt',
                'desc': 'A timeless classic, made from 100% premium cotton for ultimate comfort.',
                'variants': [
                    {'size': 'S', 'color': 'White', 'price': 19.99, 'stock': 50},
                    {'size': 'M', 'color': 'White', 'price': 19.99, 'stock': 40},
                    {'size': 'L', 'color': 'White', 'price': 19.99, 'stock': 20},
                    {'size': 'M', 'color': 'Black', 'price': 21.99, 'stock': 35},
                    {'size': 'L', 'color': 'Black', 'price': 21.99, 'stock': 15},
                ]
            },
            {
                'category': t_shirts_women,
                'name': 'Modern V-Neck Tee',
                'desc': 'A stylish and comfortable V-neck, perfect for any casual occasion.',
                'variants': [
                    {'size': 'XS', 'color': 'Red', 'price': 24.99, 'stock': 30},
                    {'size': 'S', 'color': 'Red', 'price': 24.99, 'stock': 25},
                    {'size': 'M', 'color': 'Blue', 'price': 24.99, 'stock': 10},
                ]
            },
            {
                'category': phones,
                'name': 'Galaxy Nova X',
                'desc': 'The latest in smartphone technology, with a stunning display and powerful processor.',
                'variants': [
                    {'size': '128GB', 'color': 'Cosmic Gray', 'price': 899.99, 'stock': 15},
                    {'size': '256GB', 'color': 'Cosmic Gray', 'price': 999.99, 'stock': 10},
                    {'size': '256GB', 'color': 'Aura Blue', 'price': 999.99, 'stock': 8},
                ]
            }
        ]

        for p_data in products_data:
            product = Product.objects.create(
                category=p_data['category'],
                product_name=p_data['name'],
                slug=slugify(p_data['name']),
                description=p_data['desc']
            )
            for v_data in p_data['variants']:
                ProductVariant.objects.create(
                    product=product,
                    size=v_data['size'],
                    color=v_data['color'],
                    price=v_data['price'],
                    stock_quantity=v_data['stock']
                )
        self.stdout.write(self.style.SUCCESS('Products and variants created.'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))