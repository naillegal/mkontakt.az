from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PartnerSlider, AdvertisementSlide,
    Brand, Category, Product, ProductType, ProductImage, CustomerReview, Blog,
    ContactMessage, ContactInfo, User, Wish, Cart, CartItem, DiscountCode, Order, OrderItem, BlogImage
)
from django.http import HttpResponse
import openpyxl


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount', 'created_at')
    search_fields = ('name',)


# @admin.register(ProductType)
# class ProductTypeAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ('name',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)
    fields = ('image', 'is_main', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:100px; height:80px; object-fit:cover; '
                'border:1px solid #ddd; border-radius:4px; margin:5px 0;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Şəkil önizləmə"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    exclude = ('product_types',)
    list_display = (
        'main_image_preview',
        'title',
        'priority',
        'brand',
        'get_categories',
        'price',
        'discount',
        'created_at',
    )
    list_editable = ('priority',)
    search_fields = ('title', 'brand__name')
    list_filter = ('brand', 'categories', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline]

    def get_categories(self, obj):
        return ", ".join(cat.name for cat in obj.categories.all())
    get_categories.short_description = "Kateqoriyalar"

    def main_image_preview(self, obj):
        url = obj.get_main_image_url()
        if url:
            return format_html(
                '<img src="{}" style="max-height:60px; object-fit:contain; border:1px solid #ddd;"/>',
                url
            )
        return "-"
    main_image_preview.short_description = "Əsas Şəkil"
    main_image_preview.allow_tags = True


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


class BlogImageInline(admin.TabularInline):
    model = BlogImage
    extra = 1
    readonly_fields = ('image_preview',)
    fields = ('image', 'is_main', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:100px;height:80px;object-fit:cover;'
                'border:1px solid #ddd;border-radius:4px;margin:5px 0;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Şəkil önizləmə"


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')
    inlines = [BlogImageInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'viewed', 'created_at')
    list_filter = ('viewed', 'created_at')
    search_fields = ('name', 'phone', 'email', 'message')


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = (
        'technical_label',
        'technical_email_label', 'technical_email',
        'technical_mobile_label', 'technical_mobile',
        'support_label',
        'support_email_label', 'support_email',
        'support_mobile_label', 'support_mobile',
    )
    search_fields = ('technical_email', 'support_email')


class WishInline(admin.TabularInline):
    model = Wish
    extra = 0
    can_delete = False


class CartInline(admin.TabularInline):
    model = Cart
    extra = 0
    readonly_fields = ('session_key', 'created_at', 'updated_at')
    can_delete = False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'birth_date', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    inlines = [WishInline, CartInline]

    actions = ['export_users_to_excel']

    def export_users_to_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Users"

        headers = ['Ad Soyad', 'Email', 'Telefon', 'Doğum Tarixi']
        ws.append(headers)

        for user in queryset:
            ws.append([
                user.full_name,
                user.email,
                user.phone,
                user.birth_date.strftime('%Y-%m-%d'),
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=users.xlsx'

        wb.save(response)
        return response

    export_users_to_excel.short_description = "Seçilən istifadəçiləri Excel-ə export et"


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


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
    list_display = (
        "id",
        "full_name",
        "phone",
        "product_discount",
        "category_discount",
        "total",
        "created_at"
    )
    readonly_fields = (
        "discount_amount",
        "product_discount",
        "category_discount",
        "subtotal",
        "total",
        "created_at",
    )
    fieldsets = (
        (None, {
            "fields": (
                "user",
                "full_name", "phone", "address",
                "delivery_date", "delivery_time",
            )
        }),
        ("Endirimlər", {
            "fields": (
                "discount_amount",
                "product_discount",
                "category_discount",
            )
        }),
        ("Yekun Hesablamalar", {
            "fields": ("subtotal", "total")
        }),
        ("Vaxt Stempləri", {
            "fields": ("created_at",)
        }),
    )
    inlines = [OrderItemInline]
