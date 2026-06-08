from django.test import Client, TestCase

from restaurant.tests.helpers import create_restaurant_owner


class RestaurantSpaViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner, self.brand, _token = create_restaurant_owner('spa_owner')

    def test_spa_deep_link_returns_html_not_500(self):
        self.client.force_login(self.owner)
        session = self.client.session
        session['active_brand_id'] = self.brand.pk
        session.save()
        for path in ('/restoran/dashboard', '/restoran/franchise', '/restoran/payment/success'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertNotEqual(response.status_code, 500)
                self.assertIn(response.status_code, (200, 302))
