from django.test import TestCase
from django.urls import reverse

from .models import Category, Watch, WatchImage


class HomeViewPerformanceTests(TestCase):
    def test_home_prefetches_watch_images(self):
        category = Category.objects.create(name='Dress Watches', slug='dress-watches')

        for index in range(4):
            watch = Watch.objects.create(
                name=f'Chronos {index}',
                brand='CHRONOS',
                slug=f'chronos-{index}',
                price='1999.00',
                description='A precise luxury watch.',
                features='Swiss movement, Sapphire glass',
                stock_quantity=5,
                category=category,
                is_featured=True,
                is_trending=True,
            )
            WatchImage.objects.create(
                watch=watch,
                image=f'watches/chronos-{index}.png',
                is_primary=True,
            )

        with self.assertNumQueries(4):
            response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/media/watches/chronos-0.png')
