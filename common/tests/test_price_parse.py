from decimal import Decimal

from django.test import SimpleTestCase

from common.price_parse import parse_tr_decimal


class PriceParseTests(SimpleTestCase):
    def test_tr_comma_decimal(self):
        self.assertEqual(parse_tr_decimal('1500,50'), Decimal('1500.50'))

    def test_thousands_dot(self):
        self.assertEqual(parse_tr_decimal('1.500,50'), Decimal('1500.50'))

    def test_plain_number(self):
        self.assertEqual(parse_tr_decimal('1500'), Decimal('1500'))
