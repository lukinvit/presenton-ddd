import json
import structlog
from shared.infrastructure.logging import setup_logging, get_logger

class TestLogging:
    def test_setup_logging_configures_structlog(self) -> None:
        setup_logging(json_output=False)
        logger = structlog.get_logger()
        assert logger is not None

    def test_get_logger_returns_bound_logger(self) -> None:
        setup_logging(json_output=False)
        logger = get_logger("test_domain")
        assert logger is not None

    def test_get_logger_includes_domain(self, capsys) -> None:
        setup_logging(json_output=True)
        logger = get_logger("presentation")
        logger.info("test message", key="value")
        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert parsed["domain"] == "presentation"
        assert parsed["event"] == "test message"
        assert parsed["key"] == "value"
