from controllers.dtos.health_controller_dto import HealthResponse


def get_health() -> HealthResponse:
    return {
        "message": "Contextual PII Anonymizer API",
        "version": "1.0.0",
        "status": "active",
    }
