import unittest
from app import create_app

class BasicTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app().test_client()

    def test_home_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_report_route(self):
        response = self.app.get('/report')
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
