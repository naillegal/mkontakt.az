from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.templatetags.static import static
from ckeditor.fields import RichTextField
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal


class ProductAttribute(models.Model):
    name = models.CharField(max_length=100, verbose_name="Xüsusiyyət adı")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Məhsul Xüsusiyyəti"
        verbose_name_plural = "Məhsul Xüsusiyyətləri"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name="Xüsusiyyət"
    )
    value = models.CharField(max_length=100, verbose_name="Dəyər")

    class Meta:
        verbose_name = "Xüsusiyyət Dəyəri"
        verbose_name_plural = "Xüsusiyyət Dəyərləri"
        unique_together = [("attribute", "value")]
        ordering = ["attribute__name", "value"]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="Məhsul"
    )
    code = models.CharField(
        max_length=50,
        verbose_name="Versiya kodu",
        blank=True,
        help_text="Əl ilə daxil olunur; təkrarlanma qadağası yoxdur"
    )
    attribute_values = models.ManyToManyField(
        ProductAttributeValue,
        related_name="product_variants",
        verbose_name="Xüsusiyyət dəyərləri"
    )
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Alternativ qiymət",
        help_text="Boş saxlasanız əsas məhsul qiyməti qəbul edilir"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Sıra nömrəsi"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")

    class Meta:
        verbose_name = "Məhsul Versiyası"
        verbose_name_plural = "Məhsul Versiyaları"
        ordering = ['order', 'id']

    def __str__(self):
        label = self.code or f"Variant #{self.pk}"
        return f"{self.product.title} • {label}"


class Brand(models.Model):
    name = models.CharField(max_length=255, verbose_name="Brend adı")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma tarixi")

    class Meta:
        verbose_name = "Brend"
        verbose_name_plural = "Brendlər"
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Kateqoriya adı")
    discount = models.PositiveIntegerField(
        verbose_name="Endirim faizi",
        blank=True,
        null=True,
        help_text="(İstəyə bağlı, faizlə verilir)"
    )
    image = models.ImageField(
        upload_to='categories/',
        verbose_name="Kateqoriya şəkli",
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma tarixi"
    )

    class Meta:
        verbose_name = "Kateqoriya"
        verbose_name_plural = "Kateqoriyalar"
        ordering = ['name']

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name="Alt kateqoriya"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Alt kateqoriya adı"
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name="Slug"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaradılma tarixi"
    )

    class Meta:
        verbose_name = "Alt kateqoriya"
        verbose_name_plural = "Alt kateqoriyalar"
        ordering = ['name']
        unique_together = (('category', 'name'),)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Məhsul növü")

    class Meta:
        verbose_name = "Məhsul növü"
        verbose_name_plural = "Məhsul növləri"

    def __str__(self):
        return self.name


class Product(models.Model):
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True,
        related_name='products', verbose_name="Brend"
    )
    subcategories = models.ManyToManyField(
        SubCategory,
        blank=True,
        related_name='products',
        verbose_name="Alt kateqoriyalar"
    )

    product_types = models.ManyToManyField(
        ProductType, blank=True, related_name='products', verbose_name="Məhsulun növləri"
    )

    attributes = models.ManyToManyField(
        ProductAttribute,
        blank=True,
        related_name="products",
        verbose_name="Xüsusiyyətlər"
    )

    priority = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name="Sıra nömrəsi"
    )

    code = models.CharField(
        max_length=50,
        verbose_name="Məhsul kodu",
        blank=True,
        help_text="Əl ilə daxil edilir; təkrarlanma məhdudiyyəti yoxdur"
    )

    title = models.CharField(max_length=255, verbose_name="Məhsul adı")
    slug = models.SlugField(max_length=255, unique=True,
                            verbose_name="Slug", blank=True)
    description = RichTextField(verbose_name="Təsvir", blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Qiymət")
    discount = models.PositiveIntegerField(
        verbose_name="Endirim faizi", blank=True, null=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv",
        help_text="Deaktiv edilsə, məhsul səbətə əlavə oluna bilməyəcək."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma tarixi"
    )

    class Meta:
        verbose_name = "Məhsul"
        verbose_name_plural = "Məhsullar"
        ordering = ['priority', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('MContact:product-detail', kwargs={'slug': self.slug})

    def get_main_image_url(self):
        main = self.images.filter(is_main=True).first()
        if main:
            return main.image.url
        elif self.images.exists():
            return self.images.all()[0].image.url
        return static('images/no-image.png')

    @property
    def ordered_images(self):
        return self.images.order_by('-is_main', 'order', 'id')

    @property
    def ordered_variants(self):
        return self.variants.order_by('order', 'id')


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='images', verbose_name="Məhsul"
    )
    image = models.ImageField(
        upload_to='products/', verbose_name="Məhsul şəkli"
    )
    is_main = models.BooleanField(
        default=False, verbose_name="Əsas şəkil"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Sıra nömrəsi"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yüklənmə tarixi"
    )

    class Meta:
        verbose_name = "Məhsul Şəkli"
        verbose_name_plural = "Məhsul Şəkilləri"
        ordering = ['-is_main', 'order', 'id']

    def __str__(self):
        return f"{self.product.title} - Şəkil {self.pk}"

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(
                product=self.product, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)


class PartnerSlider(models.Model):
    title = models.CharField(max_length=255, verbose_name="Başlıq")
    image = models.ImageField(upload_to='partners/', verbose_name="Şəkil")
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="partner_slides",
        verbose_name="Brend"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma tarixi")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Partnyor slayderi"
        verbose_name_plural = "Partnyor slayderləri"

    def __str__(self):
        return self.title


class AdvertisementSlide(models.Model):
    title = models.CharField(max_length=255, verbose_name="Başlıq")
    description = models.TextField(verbose_name="Təsvir")
    image = models.ImageField(
        upload_to='advertisements/', verbose_name="Şəkil")
    link = models.URLField(blank=True, null=True, verbose_name="Xüsusi keçid")

    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', verbose_name="Brend filtri"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', verbose_name="Kateqoriya filtri"
    )
    subcategory = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+', verbose_name="Alt-kateqoriya filtri"
    )
    attribute_values = models.ManyToManyField(
        ProductAttributeValue,
        blank=True,
        related_name='+',
        verbose_name="Xüsusiyyət dəyərləri filtri"
    )
    price_min = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True, verbose_name="Min. qiymət"
    )
    price_max = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True, verbose_name="Maks. qiymət"
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Reklam slaydı"
        verbose_name_plural = "Reklam slayderləri"

    def __str__(self):
        return self.title

    def build_filter_url(self):
        from django.urls import reverse
        from urllib.parse import urlencode

        base = reverse("MContact:products")
        params = {}

        if self.brand:
            params["brand"] = self.brand.id
        if self.category:
            params["category"] = self.category.id
        if self.subcategory:
            params["subcategory"] = self.subcategory.id
        if self.price_min is not None:
            params["min_price"] = str(self.price_min)
        if self.price_max is not None:
            params["max_price"] = str(self.price_max)

        for av in self.attribute_values.all():
            key = f"attr_{av.attribute.id}"
            params.setdefault(key, []).append(av.id)

        query = urlencode(params, doseq=True)
        return f"{base}?{query}" if query else base

    def build_mobile_filter_url(self):
        from django.urls import reverse
        from urllib.parse import urlencode
        from MContact.models import ProductAttribute

        base = reverse("mobile-products-filter")
        params = {}

        if self.brand_id:
            params['1'] = str(self.brand_id)
        if self.subcategory_id:
            params['2'] = str(self.subcategory_id)

        if self.attribute_values.exists():
            attr_order = list(
                ProductAttribute.objects.order_by(
                    'name').values_list('id', flat=True)
            )
            for av in self.attribute_values.all():
                idx = attr_order.index(av.attribute_id)
                key = str(idx + 3)
                params.setdefault(key, []).append(str(av.id))

        if self.price_min is not None:
            params['min_price'] = str(self.price_min)
        if self.price_max is not None:
            params['max_price'] = str(self.price_max)

        qs = urlencode(params, doseq=True)
        return f"{base}?{qs}" if qs else base

    @property
    def filter_link(self):
        return self.link or self.build_filter_url()


class CustomerReview(models.Model):
    full_name = models.CharField(
        max_length=255,
        verbose_name="Müştərinin Adı və Soyadı"
    )
    image = models.ImageField(
        upload_to='customer_reviews/',
        verbose_name="Müştəri şəkili",
        blank=True,
        null=True
    )
    review = models.TextField(
        verbose_name="Müştəri rəyi"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaradılma tarixi"
    )

    class Meta:
        verbose_name = "Müştəri Rəyi"
        verbose_name_plural = "Müştəri Rəyləri"
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name


class Blog(models.Model):
    title = models.CharField(max_length=255, verbose_name="Başlıq")
    slug = models.SlugField(max_length=255, unique=True,
                            blank=True, verbose_name="Slug")
    description = RichTextField(verbose_name="Məzmun")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma tarixi")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blog"
        verbose_name_plural = "Bloglar"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('MContact:blog-detail', kwargs={'slug': self.slug})

    def get_default_image(self):
        main = self.images.filter(is_main=True).first()
        if main:
            return main.image.url
        elif self.images.exists():
            return self.images.first().image.url
        if self.image:
            return self.image.url
        return static('images/blog.png')

    @property
    def ordered_images(self):
        return self.images.order_by('-is_main', '-created_at')


class BlogImage(models.Model):
    blog = models.ForeignKey(
        Blog, on_delete=models.CASCADE,
        related_name='images', verbose_name="Blog"
    )
    image = models.ImageField(
        upload_to='blogs/', verbose_name="Blog şəkli"
    )
    is_main = models.BooleanField(
        default=False, verbose_name="Əsas şəkil"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yüklənmə tarixi"
    )

    class Meta:
        verbose_name = "Blog Şəkli"
        verbose_name_plural = "Blog Şəkilləri"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.blog.title} – Şəkil {self.pk}"

    def save(self, *args, **kwargs):
        if self.is_main:
            BlogImage.objects.filter(
                blog=self.blog, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    name = models.CharField(max_length=255, verbose_name="Ad")
    company = models.CharField(
        max_length=255, verbose_name="Şirkət", blank=True, null=True)
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    phone = models.CharField(max_length=50, verbose_name="Telefon")
    message = models.TextField(verbose_name="İsmarıc", blank=True)
    viewed = models.BooleanField(default=False, verbose_name="Baxdım")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Göndərilmə tarixi")

    class Meta:
        verbose_name = "Əlaqə Mesajı"
        verbose_name_plural = "Əlaqə Mesajları"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ContactInfo(models.Model):
    technical_label = models.CharField(
        max_length=100,
        default="Texniki sorğular",
        verbose_name="Texniki bölmə başlığı"
    )
    technical_email_label = models.CharField(
        max_length=50,
        default="E-mail",
        verbose_name="Texniki bölmə E-mail etiket"
    )
    technical_mobile_label = models.CharField(
        max_length=50,
        default="Mobil",
        verbose_name="Texniki bölmə Mobil etiket"
    )
    support_label = models.CharField(
        max_length=100,
        default="Dəstək xidməti",
        verbose_name="Dəstək bölməsi başlığı"
    )
    support_email_label = models.CharField(
        max_length=50,
        default="E-mail",
        verbose_name="Dəstək bölməsi E-mail etiketi"
    )
    support_mobile_label = models.CharField(
        max_length=50,
        default="Mobil",
        verbose_name="Dəstək bölməsi Mobil etiketi"
    )
    technical_email = models.EmailField(verbose_name="Texniki Email")
    technical_mobile = models.CharField(
        max_length=50, verbose_name="Texniki Mobil")
    support_email = models.EmailField(verbose_name="Dəstək Email")
    support_mobile = models.CharField(
        max_length=50, verbose_name="Dəstək Mobil")
    instagram = models.URLField(
        blank=True, null=True, verbose_name="Instagram")
    facebook = models.URLField(blank=True, null=True, verbose_name="Facebook")
    whatsapp = models.URLField(blank=True, null=True, verbose_name="WhatsApp")
    youtube = models.URLField(blank=True, null=True, verbose_name="YouTube")

    class Meta:
        verbose_name = "Əlaqə Məlumatı"
        verbose_name_plural = "Əlaqə Məlumatları"

    def __str__(self):
        return "Əlaqə Məlumatları"


class User(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="Ad Soyad")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=50, verbose_name="Telefon")
    birth_date = models.DateField(verbose_name="Doğum Tarixi")
    password = models.CharField(max_length=128, verbose_name="Parol")
    image = models.ImageField(upload_to='user_images/',
                              blank=True, null=True, verbose_name="Şəkil")

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma Tarixi")

    class Meta:
        verbose_name = "İstifadəçi"
        verbose_name_plural = "İstifadəçilər"

    def __str__(self):
        return self.full_name


class Wish(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishes")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wished_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        verbose_name = "İstək siyahısı elementi"
        verbose_name_plural = "İstək siyahısı"

    def __str__(self):
        return f"{self.user.full_name} → {self.product.title}"


class Cart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Səbət elementi"
        verbose_name_plural = "Səbət"

    def __str__(self):
        who = self.user.full_name if self.user else f"session:{self.session_key}"
        return f"Cart • {who}"

    @property
    def raw_total(self):
        return sum(
            item.unit_price * item.quantity
            for item in self.items.select_related("product", "variant")
        )

    @property
    def product_discount(self):
        total = Decimal('0')
        seen = set()
        for item in self.items.select_related("product").all():
            p = item.product
            if p.discount and p.id not in seen:
                frac = Decimal(p.discount) / Decimal('100')
                total += p.price * frac
                seen.add(p.id)
        return total

    @property
    def category_discount(self):
        total = Decimal('0')
        cat_products: dict[Category, set[Product]] = {}
        for item in self.items.select_related("product").all():
            p = item.product
            for sub in p.subcategories.all():
                cat = sub.category
                if cat.discount:
                    cat_products.setdefault(cat, set()).add(p)
        for cat, products in cat_products.items():
            frac = Decimal(cat.discount) / Decimal('100')
            subtotal = sum(prod.price for prod in products)
            total += subtotal * frac
        return total

    def get_discount_code_amount(self):
        if not hasattr(self, "discountcodeuse"):
            return 0
        return (self.raw_total - self.product_discount) * self.discountcodeuse.code.percent / 100

    @property
    def grand_total(self):
        return (
            self.raw_total
            - self.product_discount
            - self.category_discount
            - self.get_discount_code_amount()
        )


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Səbət məhsulu"
        verbose_name_plural = "Səbət məhsulları"
        unique_together = ("cart", "product", "variant")

    @property
    def unit_price(self):
        if self.variant and self.variant.price_override is not None:
            return self.variant.price_override
        return self.product.price

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    @property
    def selected_attrs(self):
        if not self.variant:
            return []
        return [
            {"name": v.attribute.name, "value": v.value}
            for v in self.variant.attribute_values.all()
        ]

    def __str__(self):
        return f"{self.product.title} x{self.quantity}"


class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    percent = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Endirim kodu"
        verbose_name_plural = "Endirim kodları"

    def __str__(self):
        return f"{self.code} ({self.percent}%)"


class DiscountCodeUse(models.Model):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    code = models.ForeignKey(DiscountCode, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Endirim kodu istifadəsi"
        verbose_name_plural = "Endirim kodu istifadələri"

    def __str__(self):
        return f"{self.cart} → {self.code}"


class Order(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="İstifadəçi"
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name="Tam Ad"
    )
    phone = models.CharField(
        max_length=50,
        verbose_name="Telefon"
    )
    address = models.TextField(
        verbose_name="Ünvan"
    )
    delivery_date = models.DateField(
        verbose_name="Çatdırılma Tarixi"
    )
    delivery_time = models.TimeField(
        verbose_name="Çatdırılma Vaxtı"
    )
    discount_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Endirim Kodu"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Endirim Məbləği"
    )
    product_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Məhsul Endirimi"
    )
    category_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2, default=0,
        verbose_name="Kateqoriya Endirimi"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Ara Cəm"
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Ümumi Məbləğ"
    )
    shipping_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Çatdırılma haqqı"
    )
    viewed = models.BooleanField(
        default=False,
        verbose_name="Baxdım",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaradılma Tarixi"
    )

    class Meta:
        verbose_name = "Sifariş"
        verbose_name_plural = "Sifarişlər"

    def __str__(self):
        return f"Sifariş #{self.pk}"

    @property
    def shipping_fee(self) -> Decimal:
        return Decimal('0.00') if self.total >= Decimal('200.00') else Decimal('10.00')
    shipping_fee.fget.short_description = "Çatdırılma haqqı"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Sifariş"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Məhsul"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="+"
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Miqdar"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Vahid Qiymət"
    )

    class Meta:
        verbose_name = "Sifariş Məhsulu"
        verbose_name_plural = "Sifariş Məhsulları"

    def __str__(self):
        return f"{self.order} • {self.product.title}"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    class Meta:
        verbose_name = "Şifrə sıfırlama OTP"
        verbose_name_plural = "Şifrə sıfırlama OTP-lər"

    def __str__(self):
        return f"{self.user.email} – {self.code}"


class UserDeviceToken(models.Model):
    PLATFORM_CHOICES = (
        ('android', 'Android'),
        ('ios', 'iOS'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="device_tokens", null=True, blank=True)
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cihaz tokeni"
        verbose_name_plural = "Cihaz tokenləri"

    def __str__(self):
        owner = self.user.full_name if self.user else "Anon"
        return f"{owner} • {self.platform}"


class SiteConfiguration(models.Model):
    navbar_logo = models.ImageField(
        upload_to="logos/",
        verbose_name="Navbar Logo",
        blank=True,
        null=True,
        help_text="Yuxarıdakı navbar-da göstəriləcək logo"
    )

    class Meta:
        verbose_name = "Sayt Konfiqurasiyası"
        verbose_name_plural = "Sayt Konfiqurasiyaları"

    def __str__(self):
        return "Sayt Konfiqurasiyası"

    @property
    def navbar_logo_url(self):
        if self.navbar_logo:
            return self.navbar_logo.url
        return static("images/mcontact-blue-logo.png")


class HomePageBanner(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="Banner başlığı"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Banner təsviri"
    )
    image = models.ImageField(
        upload_to='home_banners/',
        verbose_name="Banner şəkli"
    )
    link = models.URLField(
        blank=True,
        verbose_name="Ətraflı keçid URL-i"
    )
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='+')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='+')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='+')
    attribute_values = models.ManyToManyField(
        ProductAttributeValue, blank=True, related_name='+')
    price_min = models.DecimalField(max_digits=10, decimal_places=2,
                                    null=True, blank=True)
    price_max = models.DecimalField(max_digits=10, decimal_places=2,
                                    null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaradılma tarixi"
    )

    class Meta:
        verbose_name = "Əsas səhifə – İlk reklam"
        verbose_name_plural = "Əsas səhifə – İlk reklam"

    def __str__(self):
        return self.title

    def build_filter_url(self):
        from django.urls import reverse
        from urllib.parse import urlencode
        base = reverse("MContact:products")
        params = {}
        if self.brand_id:
            params["brand"] = self.brand_id
        if self.category_id:
            params["category"] = self.category_id
        if self.subcategory_id:
            params["subcategory"] = self.subcategory_id
        if self.price_min is not None:
            params["min_price"] = str(self.price_min)
        if self.price_max is not None:
            params["max_price"] = str(self.price_max)
        for av in self.attribute_values.all():
            key = f"attr_{av.attribute_id}"
            params.setdefault(key, []).append(av.id)
        qs = urlencode(params, doseq=True)
        return f"{base}?{qs}" if qs else base

    def build_mobile_filter_url(self):
        from django.urls import reverse
        from urllib.parse import urlencode
        from MContact.models import ProductAttribute
        base = reverse("mobile-products-filter")
        params = {}
        if self.brand_id:
            params["1"] = str(self.brand_id)
        if self.subcategory_id:
            params["2"] = str(self.subcategory_id)
        if self.attribute_values.exists():
            order = list(ProductAttribute.objects.order_by("name")
                         .values_list("id", flat=True))
            for av in self.attribute_values.all():
                idx = order.index(av.attribute_id)
                params.setdefault(str(idx + 3), []).append(str(av.id))
        if self.price_min is not None:
            params["min_price"] = str(self.price_min)
        if self.price_max is not None:
            params["max_price"] = str(self.price_max)
        qs = urlencode(params, doseq=True)
        return f"{base}?{qs}" if qs else base

    @property
    def filter_link(self):
        return self.link or self.build_filter_url()


class RegistrationOTP(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    birth_date = models.DateField()
    password = models.CharField(max_length=128)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.email} – {self.code}"


class PushNotification(models.Model):
    title = models.CharField(max_length=120)
    message = models.TextField()
    recipients = models.ManyToManyField(User, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bildiriş"
        verbose_name_plural = "Bildirişlər"

    def __str__(self):
        return f"{self.title} ({self.created_at:%d.%m %H:%M})"

    def send(self) -> int:
        from .models import UserDeviceToken
        from .utils import send_push

        tokens = list(
            UserDeviceToken.objects
            .filter(user__in=self.recipients.all())
            .values_list("token", flat=True)
        )
        send_push(tokens, self.title, self.message)
        return len(tokens)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Branch(models.Model):
    name = models.CharField(max_length=150)
    iframe_src = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Filial"
        verbose_name_plural = "Filiallar"

    def __str__(self):
        return self.name
