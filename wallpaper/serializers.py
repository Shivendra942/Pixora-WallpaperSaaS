from rest_framework import serializers
from .models import Wallpaper, WallpaperImage

class WallpaperImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WallpaperImage
        fields = ['image']


class WallpaperSerializer(serializers.ModelSerializer):
    images = WallpaperImageSerializer(many=True, read_only=True)

    class Meta:
        model = Wallpaper
        fields = '__all__'