from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Wallpaper(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='wallpapers/')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    downloads = models.IntegerField(default=0)
    is_paid = models.BooleanField(default=False)
    price = models.IntegerField(default=0)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Wallpaper"
        verbose_name_plural = "Wallpapers"

   
class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wallpaper = models.ForeignKey(Wallpaper, on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)
    amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wallpaper = models.ForeignKey(Wallpaper, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'wallpaper')

class WallpaperImage(models.Model):
    wallpaper = models.ForeignKey(
        Wallpaper,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='wallpapers/')