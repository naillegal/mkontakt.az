from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.templatetags.static import static
from ckeditor.fields import RichTextField


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
    image = models.ImageField(
        upload_to='categories/',
        verbose_name="Kateqoriya şəkli",
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma tarixi")

    class Meta:
        verbose_name = "Kateqoriya"
        verbose_name_plural = "Kateqoriyalar"
        ordering = ['name']

    def __str__(self):
        return self.name


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
    categories = models.ManyToManyField(
        Category, blank=True, related_name='products', verbose_name="Kateqoriyalar"
    )

    product_types = models.ManyToManyField(
        ProductType, blank=True, related_name='products', verbose_name="Məhsulun növləri"
    )

    title = models.CharField(max_length=255, verbose_name="Məhsul adı")
    slug = models.SlugField(max_length=255, unique=True,
                            verbose_name="Slug", blank=True)
    description = models.TextField(verbose_name="Təsvir", blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Qiymət")
    discount = models.PositiveIntegerField(
        verbose_name="Endirim faizi", blank=True, null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma tarixi"
    )

    class Meta:
        verbose_name = "Məhsul"
        verbose_name_plural = "Məhsullar"
        ordering = ['-created_at']

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
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yüklənmə tarixi"
    )

    class Meta:
        verbose_name = "Məhsul Şəkli"
        verbose_name_plural = "Məhsul Şəkilləri"
        ordering = ['-created_at']

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
    link = models.URLField(blank=True, null=True, verbose_name="Keçid")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Yaradılma tarixi")

    class Meta:
        ordering = ['created_at']
        verbose_name = "Reklam slayderi"
        verbose_name_plural = "Reklam slayderləri"

    def __str__(self):
        return self.title


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
    image = models.ImageField(
        upload_to='blogs/', blank=True, null=True, verbose_name="Şəkil")
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
        if self.image:
            return self.image.url
        return static('images/blog.png')


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
        return sum(i.product.price * i.quantity for i in self.items.select_related("product"))

    @property
    def product_discount(self):
        return sum(
            i.product.price * i.product.discount / 100 * i.quantity
            for i in self.items.select_related("product") if i.product.discount
        )

    def get_discount_code_amount(self):
        if not hasattr(self, "discountcodeuse"):
            return 0
        return (self.raw_total - self.product_discount) * self.discountcodeuse.code.percent / 100

    @property
    def grand_total(self):
        return self.raw_total - self.product_discount - self.get_discount_code_amount()


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Səbət məhsulu"
        verbose_name_plural = "Səbət məhsulları"
        unique_together = ("cart", "product")

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
        User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    address = models.TextField()
    delivery_date = models.DateField()
    delivery_time = models.TimeField()
    discount_code = models.CharField(max_length=50, blank=True)
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    product_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sifariş"
        verbose_name_plural = "Sifarişlər"

    def __str__(self):
        return f"Sifariş #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Sifariş məhsulu"
        verbose_name_plural = "Sifariş məhsulları"

    def __str__(self):
        return f"{self.order} • {self.product.title}"
