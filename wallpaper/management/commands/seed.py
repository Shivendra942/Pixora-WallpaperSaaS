from django.core.management.base import BaseCommand
from faker import Faker
import random
import os
from wallpaper.models import Wallpaper, Category
from django.core.files import File

fake = Faker()

class Command(BaseCommand):
    help = "Seed database"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding...")

        categories = []
        for _ in range(5):
            cat, _ = Category.objects.get_or_create(
                name=fake.word(),
                slug=fake.slug()
            )
            categories.append(cat)

        IMAGE_FOLDER = "media/sample/"
        images = os.listdir(IMAGE_FOLDER)

        for _ in range(20):
            category = random.choice(categories)
            image_file = random.choice(images)

            with open(os.path.join(IMAGE_FOLDER, image_file), 'rb') as f:
                wallpaper = Wallpaper.objects.create(
                    title=fake.sentence(nb_words=3),
                    description=fake.text(),
                    category=category,
                    is_paid=random.choice([True, False]),
                    price=random.randint(10, 200)
                )

                wallpaper.image.save(image_file, File(f), save=True)

        self.stdout.write(self.style.SUCCESS("Done!"))