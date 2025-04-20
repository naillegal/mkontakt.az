from django.contrib import admin
from .models import (
    PartnerSlider, AdvertisementSlide,
    Brand, Category, Product, ProductType, ProductImage, CustomerReview, Blog,
    ContactMessage, ContactInfo, User, Wish, Cart, CartItem, DiscountCode, Order, OrderItem
)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'brand', 'get_categories',
                    'price', 'discount', 'created_at')
    search_fields = ('title', 'brand__name')
    list_filter = ('brand', 'categories', 'created_at')
    prepopulated_fields = {'slug': ('title',)}

    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])
    get_categories.short_description = "Kateqoriyalar"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'is_main', 'created_at')
    list_editable = ('is_main',)
    search_fields = ('product__title',)
    list_filter = ('product', 'is_main')


@admin.register(PartnerSlider)
class PartnerSliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)


@admin.register(AdvertisementSlide)
class AdvertisementSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'description')


@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'created_at')
    search_fields = ('full_name', 'review')


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'viewed', 'created_at')
    list_filter = ('viewed', 'created_at')
    search_fields = ('name', 'phone', 'email', 'message')


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ('technical_email', 'technical_mobile',
                    'support_email', 'support_mobile')
    search_fields = ('technical_email', 'support_email')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'birth_date', 'created_at')
    search_fields = ('full_name', 'email', 'phone')


@admin.register(Wish)
class WishAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    search_fields = ("user__full_name", "product__title")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "created_at", "updated_at")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity")


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "percent", "active", "expires_at")
    list_filter = ("active",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone", "total", "created_at")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "unit_price")
