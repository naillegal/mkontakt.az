from django.urls import path
from . import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

app_name = 'MContact'

schema_view = get_schema_view(
    openapi.Info(
        title="MContact API List",
        default_version='v1',
        description="MContact üçün API endpointləri",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('api/swagger/', schema_view.with_ui('swagger'), name='schema-swagger-ui'),
    path('', views.index, name='index'),
    path('haqqımızda/', views.about_us, name='about_us'),
    path('qaydalar/', views.rules, name='rules'),
    path('şifrə-bərpası/', views.forget_password, name='forget-password'),
    path('otp/', views.otp, name='otp'),
    path('yeni-şifrə/', views.new_password, name='new-password'),
    path('məhsullar/', views.products, name='products'),
    path('məhsullar/<slug:slug>/', views.product_detail, name='product-detail'),
    path('api/brands/', views.BrandListCreateAPIView.as_view(),
         name='brand-list-create'),
    path('api/categories/', views.CategoryListCreateAPIView.as_view(),
         name='category-list-create'),
    #     path('api/product-types/', views.ProductTypeListCreateAPIView.as_view(),
    #          name='producttype-list-create'),
    path('api/products/', views.ProductListAPIView.as_view(), name='product-list'),
    path('api/products/<int:pk>/',
         views.ProductRetrieveAPIView.as_view(), name='product-detail'),
    path('api/partners/', views.PartnerSliderListCreateAPIView.as_view(),
         name='partner-slider-list'),
    path('api/advertisements/', views.AdvertisementSlideListAPIView.as_view(),
         name='advertisement-slide-list'),
    path('api/customer-reviews/', views.CustomerReviewListCreateAPIView.as_view(),
         name='customer-review-list-create'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog-detail'),
    path('api/blogs/', views.BlogListCreateAPIView.as_view(),
         name='blog-list-create'),
    path('api/blogs/<slug:slug>/',
         views.BlogRetrieveUpdateDestroyAPIView.as_view(), name='blog-detail-api'),
    path('əlaqə/', views.contact, name='contact'),
    path('contact/submit/', views.contact_submit, name='contact-submit'),
    path('api/register/', views.RegisterAPIView.as_view(),   name='user-register'),
    path('api/register-otp/', views.RegisterOTPAPIView.as_view(), name='register-otp'),
    path('api/login/', views.UserLoginAPIView.as_view(), name='user-login'),
    path('api/users/', views.UserListAPIView.as_view(), name='user-list'),
    path('api/users/<int:pk>/',
         views.UserRetrieveAPIView.as_view(), name='user-detail'),
    path('qeydiyyat/', views.register, name='register'),
    path('qeydiyyat/otp/', views.register_otp, name='register-otp'),
    path('giriş/', views.login_view, name='login'),
    path('profil-düzəlişi/', views.edit_profile, name='edit_profile'),
    path('api/update-profile/', views.UserProfileUpdateAPIView.as_view(),
         name='user-profile-update'),
    path("şifrəni-dəyiş/", views.change_password, name="change_password"),
    path("api/change-password/", views.ChangePasswordAPIView.as_view(),
         name="change-password"),
    path("istək-siyahısı/", views.wishlist_view, name="wishlist_view"),
    path("wishlist/toggle/<int:product_id>/",
         views.toggle_wishlist, name="wishlist-toggle"),
    path("səbət/", views.cart_view, name="cart_view"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart-add"),
    path("cart/update/", views.cart_update,
         name="cart-update"),
    path("cart/apply-discount/", views.apply_discount, name="cart-discount"),
    path('sifariş/', views.order_view, name='order'),
    path("order/create/", views.order_create, name="order-create"),
    path('çıxış/', views.logout_view, name='logout'),
    path('api/logout/', views.LogoutAPIView.as_view(), name='api-logout'),
    path('api/forgot-password/', views.ForgotPasswordAPIView.as_view(),
         name='api-forgot-password'),
    path('api/verify-otp/', views.VerifyOtpAPIView.as_view(), name='api-verify-otp'),
    path('api/update-password/', views.UpdatePasswordAPIView.as_view(),
         name='api-update-password'),
    path("api/mobile-cart/", views.MobileCartView.as_view(), name="mobile-cart"),
    path(
        'api/discount-codes/',
        views.DiscountCodeListCreateAPIView.as_view(),
        name='discountcode-list-create'
    ),
    path(
        'api/calculate-discount/',
        views.CalculateDiscountPercentageAPIView.as_view(),
        name='calculate-discount'
    ),
    path(
        'api/wishlist/',
        views.WishlistAPIView.as_view(),
        name='api-wishlist'
    ),
    path(
        "api/mobile-orders/",
        views.MobileOrderView.as_view(),
        name="mobile-orders"
    ),
    path(
        'api/category-products/<int:category_id>/',
        views.CategoryProductsAPIView.as_view(),
        name='category-products'
    ),
    path(
        'api/device-token/',
        views.RegisterDeviceTokenAPIView.as_view(),
        name='device-token'
    ),
    path("api/products/filter/",
         views.MobileProductFilterAPIView.as_view(),
         name="mobile-products-filter"),
    path('api/attributes/', views.AttributeListAPIView.as_view(), name='attribute-list'),
]
