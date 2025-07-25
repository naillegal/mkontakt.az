from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="MContact API",
        default_version='v1',
        description="MContact üçün API endpointləri",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('brands/', views.BrandListCreateAPIView.as_view(), name='brand-list-create'),
    path('categories/', views.CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('products/', views.ProductListAPIView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductRetrieveAPIView.as_view(), name='product-detail'),
    path('products/filter/', views.MobileProductFilterAPIView.as_view(), name='mobile-products-filter'),
    path('category-products/<int:category_id>/', views.CategoryProductsAPIView.as_view(), name='category-products'),
    path('partners/', views.PartnerSliderListCreateAPIView.as_view(), name='partner-slider-list'),
    path('advertisements/', views.AdvertisementSlideListAPIView.as_view(), name='advertisement-slide-list'),
    path('customer-reviews/', views.CustomerReviewListCreateAPIView.as_view(), name='customer-review-list-create'),
    path('blogs/', views.BlogListCreateAPIView.as_view(), name='blog-list-create'),
    path('blogs/<slug:slug>/', views.BlogRetrieveUpdateDestroyAPIView.as_view(), name='blog-detail-api'),
    path('register/', views.RegisterAPIView.as_view(), name='user-register'),
    path('register-otp/', views.RegisterOTPAPIView.as_view(), name='register-otp'),
    path('login/', views.UserLoginAPIView.as_view(), name='user-login'),
    path('logout/', views.LogoutAPIView.as_view(), name='api-logout'),
    path('users/', views.UserListAPIView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserRetrieveAPIView.as_view(), name='user-detail'),
    path('update-profile/', views.UserProfileUpdateAPIView.as_view(), name='user-profile-update'),
    path('change-password/', views.ChangePasswordAPIView.as_view(), name='change-password'),
    path('forgot-password/', views.ForgotPasswordAPIView.as_view(), name='api-forgot-password'),
    path('verify-otp/', views.VerifyOtpAPIView.as_view(), name='api-verify-otp'),
    path('update-password/', views.UpdatePasswordAPIView.as_view(), name='api-update-password'),
    path('mobile-cart/', views.MobileCartView.as_view(), name='mobile-cart'),
    path('mobile-orders/', views.MobileOrderView.as_view(), name='mobile-orders'),
    path('discount-codes/', views.DiscountCodeListCreateAPIView.as_view(), name='discountcode-list-create'),
    path('calculate-discount/', views.CalculateDiscountPercentageAPIView.as_view(), name='calculate-discount'),
    path('wishlist/', views.WishlistAPIView.as_view(), name='api-wishlist'),
    path('device-token/', views.RegisterDeviceTokenAPIView.as_view(), name='device-token'),
    path('attributes/', views.AttributeListAPIView.as_view(), name='attribute-list'),
    path('attribute/names/', views.AttributeNameListAPIView.as_view(), name='attribute-names'),
    path('attribute-values/<int:attribute_id>/', views.AttributeValueByAttributeAPIView.as_view(), name='attribute-values'),
    path('filter-options/', views.FilterOptionsListAPIView.as_view(), name='options-list'),
    path('filter-options/<int:option_id>/', views.FilterOptionValuesAPIView.as_view(), name='filter-options-values'),
    path('notifications/broadcast/', views.BroadcastNotificationView.as_view(), name='broadcast-notification'),
]
