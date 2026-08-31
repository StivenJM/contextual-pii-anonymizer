import unittest

from fastapi.testclient import TestClient

from app.main import create_app


class HttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_root_describes_the_service(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "message": "Contextual PII Anonymizer API",
                "version": "1.0.0",
                "status": "active",
            },
        )

    def test_health_reports_service_status(self) -> None:
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "message": "Contextual PII Anonymizer API",
                "version": "1.0.0",
                "status": "active",
            },
        )

    def test_unknown_endpoint_uses_public_error_contract(self) -> None:
        response = self.client.get("/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"message": "Endpoint not found"})

    def test_unhandled_error_uses_public_error_contract(self) -> None:
        @self.app.get("/failure")
        def fail() -> None:
            raise RuntimeError("private detail")

        response = self.client.get("/failure")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"message": "Internal server error"})


if __name__ == "__main__":
    unittest.main()
