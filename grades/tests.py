from django.test import TestCase
from django.test import Client
from .models import Assignment, Submission

# Create your tests here.
class GradingAppTests(TestCase):
    def setUp(self):
        return super().setUp()
    
    def test_login_page(self):
        client = Client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Login" in str(response.content))