import unittest
from unittest.mock import patch
from services.airtable import send_to_airtable

class TestAirtableService(unittest.TestCase):
    @patch("requests.post")
    def test_send_to_airtable_success(self, mock_post):
        mock_post.return_value.status_code = 200
        result = send_to_airtable("test_action", {"key": "value"})
        self.assertTrue(result)

    @patch("requests.post")
    def test_send_to_airtable_with_photo(self, mock_post):
        mock_post.return_value.status_code = 200
        with patch("builtins.open", mock_open(read_data=b"photo_data")):
            result = send_to_airtable("test_action", {"key": "value"}, "test.jpg")
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()