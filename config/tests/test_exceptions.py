from django.test import SimpleTestCase
from rest_framework.exceptions import NotFound, ValidationError

from config.exceptions import exception_handler


class ExceptionHandlerReshapeTests(SimpleTestCase):
    def test_not_found_reshapes_detail_to_error(self):
        response = exception_handler(NotFound("Thing not found"), {})
        self.assertEqual(response.data, {"error": "Thing not found"})

    def test_validation_error_string_reshapes_list_to_error(self):
        response = exception_handler(ValidationError("Bad input"), {})
        self.assertEqual(response.data, {"error": "Bad input"})

    def test_unhandled_exception_returns_none(self):
        self.assertIsNone(exception_handler(ValueError("not a DRF exception"), {}))
