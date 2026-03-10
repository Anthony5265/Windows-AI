"""
Comprehensive unit tests for Error Handling System

Tests structured logging, error classification, and health checking
"""

import pytest
import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, mock_open
from datetime import datetime

from windows_ai.core.error_handling import (
    ErrorSeverity,
    ErrorCategory,
    StructuredLogger,
    JSONFormatter,
    ErrorHandler,
    ErrorWithContext,
    HealthChecker,
    get_logger
)


class TestErrorEnums:
    """Test error enumeration types"""

    def test_error_severity_values(self):
        """Test ErrorSeverity enum values"""
        assert ErrorSeverity.DEBUG.value == "debug"
        assert ErrorSeverity.INFO.value == "info"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_error_category_values(self):
        """Test ErrorCategory enum values"""
        assert ErrorCategory.PLUGIN.value == "plugin"
        assert ErrorCategory.API.value == "api"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.SYSTEM.value == "system"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestStructuredLogger:
    """Test StructuredLogger functionality"""

    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        """Create temporary log directory"""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        return log_dir

    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create logger instance for testing"""
        return StructuredLogger("test_logger", log_dir=temp_log_dir)

    def test_logger_init(self, temp_log_dir):
        """Test logger initialization"""
        logger = StructuredLogger("test", log_dir=temp_log_dir)
        assert logger.name == "test"
        assert logger.log_dir == temp_log_dir
        assert isinstance(logger.context, dict)
        assert len(logger.context) == 0

    def test_logger_creates_log_directory(self, tmp_path):
        """Test that logger creates log directory if it doesn't exist"""
        log_dir = tmp_path / "new_logs"
        logger = StructuredLogger("test", log_dir=log_dir)
        assert log_dir.exists()

    def test_logger_uses_default_dir(self):
        """Test that logger uses default directory when not specified"""
        with patch('pathlib.Path.mkdir'):
            logger = StructuredLogger("test")
            expected_dir = Path.home() / ".windows_ai" / "logs"
            assert logger.log_dir == expected_dir

    def test_set_context(self, logger):
        """Test setting persistent context"""
        logger.set_context(user_id="123", session="abc")
        assert logger.context["user_id"] == "123"
        assert logger.context["session"] == "abc"

    def test_clear_context(self, logger):
        """Test clearing context"""
        logger.set_context(key="value")
        logger.clear_context()
        assert len(logger.context) == 0

    def test_request_context(self, logger):
        """Test thread-local request context"""
        logger.set_request_context(request_id="req123")
        assert hasattr(logger.local, 'context')
        assert logger.local.context["request_id"] == "req123"

    def test_clear_request_context(self, logger):
        """Test clearing request context"""
        logger.set_request_context(key="value")
        logger.clear_request_context()
        assert len(logger.local.context) == 0

    def test_get_full_context(self, logger):
        """Test combining persistent and request context"""
        logger.set_context(persistent="value1")
        logger.set_request_context(request="value2")

        full_context = logger._get_full_context()
        assert full_context["persistent"] == "value1"
        assert full_context["request"] == "value2"

    def test_log_debug(self, logger):
        """Test debug logging"""
        with patch.object(logger.logger, 'debug') as mock_debug:
            logger.debug("Test message", extra_data="value")
            mock_debug.assert_called_once()
            args, kwargs = mock_debug.call_args
            assert "Test message" in args
            assert "extra" in kwargs

    def test_log_info(self, logger):
        """Test info logging"""
        with patch.object(logger.logger, 'info') as mock_info:
            logger.info("Info message")
            mock_info.assert_called_once()

    def test_log_warning(self, logger):
        """Test warning logging"""
        with patch.object(logger.logger, 'warning') as mock_warning:
            logger.warning("Warning message")
            mock_warning.assert_called_once()

    def test_log_error(self, logger):
        """Test error logging"""
        with patch.object(logger.logger, 'error') as mock_error:
            logger.error("Error message", exc_info=True)
            mock_error.assert_called_once()
            args, kwargs = mock_error.call_args
            assert kwargs.get('exc_info') is True

    def test_log_critical(self, logger):
        """Test critical logging"""
        with patch.object(logger.logger, 'critical') as mock_critical:
            logger.critical("Critical message")
            mock_critical.assert_called_once()

    def test_log_exception(self, logger):
        """Test exception logging with traceback"""
        with patch.object(logger.logger, 'exception') as mock_exception:
            logger.exception("Exception occurred")
            mock_exception.assert_called_once()


class TestJSONFormatter:
    """Test JSON log formatting"""

    @pytest.fixture
    def formatter(self):
        """Create formatter instance"""
        return JSONFormatter()

    def test_format_basic_record(self, formatter):
        """Test formatting a basic log record"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test"
        record.funcName = "test_func"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "Test message"
        assert data["module"] == "test"
        assert data["function"] == "test_func"
        assert data["line"] == 10

    def test_format_with_context(self, formatter):
        """Test formatting record with context"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.module = "test"
        record.funcName = "test_func"
        record.context = {"user_id": "123"}

        result = formatter.format(record)
        data = json.loads(result)

        assert "context" in data
        assert data["context"]["user_id"] == "123"

    def test_format_with_exception(self, formatter):
        """Test formatting record with exception info"""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        record.module = "test"
        record.funcName = "test_func"

        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "Test error" in data["exception"]["message"]
        assert "traceback" in data["exception"]


class TestErrorHandler:
    """Test ErrorHandler functionality"""

    @pytest.fixture
    def logger(self):
        """Create mock logger"""
        mock_logger = Mock(spec=StructuredLogger)
        mock_logger.logger = Mock()
        mock_logger.logger.level = logging.INFO
        return mock_logger

    @pytest.fixture
    def error_handler(self, logger):
        """Create error handler instance"""
        return ErrorHandler(logger)

    def test_error_handler_init(self, error_handler):
        """Test error handler initialization"""
        assert error_handler.logger is not None
        assert isinstance(error_handler.error_messages, dict)
        assert len(error_handler.error_messages) > 0

    def test_handle_error_basic(self, error_handler, logger):
        """Test basic error handling"""
        error = RuntimeError("Test error")

        result = error_handler.handle_error(error)

        assert result["category"] == ErrorCategory.UNKNOWN.value
        assert result["severity"] == ErrorSeverity.ERROR.value
        assert "message" in result
        assert "technical_details" in result
        assert result["technical_details"] == "Test error"

    def test_handle_error_with_context(self, error_handler, logger):
        """Test error handling with context"""
        error = ValueError("Invalid value")
        context = {"field": "username", "value": "test"}

        result = error_handler.handle_error(
            error,
            category=ErrorCategory.CONFIGURATION,
            context=context
        )

        assert result["context"] == context
        assert result["category"] == ErrorCategory.CONFIGURATION.value

    def test_handle_error_api_key_detection(self, error_handler, logger):
        """Test detection of API key errors"""
        error = RuntimeError("API key invalid")
        context = {"service": "openai"}

        result = error_handler.handle_error(
            error,
            category=ErrorCategory.API,
            context=context
        )

        assert "openai" in result["message"]
        assert "API key" in result["message"]

    def test_handle_error_rate_limit_detection(self, error_handler, logger):
        """Test detection of rate limit errors"""
        error = RuntimeError("Rate limit exceeded")
        context = {"service": "anthropic"}

        result = error_handler.handle_error(
            error,
            category=ErrorCategory.API,
            context=context
        )

        assert "Rate limit" in result["message"]

    def test_handle_error_timeout_detection(self, error_handler, logger):
        """Test detection of timeout errors"""
        error = TimeoutError("Request timed out")
        context = {"service": "google"}

        result = error_handler.handle_error(
            error,
            category=ErrorCategory.API,
            context=context
        )

        assert "timeout" in result["message"].lower()

    def test_handle_error_network_detection(self, error_handler, logger):
        """Test detection of network errors"""
        error = ConnectionError("Network error")
        context = {"service": "test"}

        result = error_handler.handle_error(
            error,
            category=ErrorCategory.NETWORK,
            context=context
        )

        assert "network" in result["message"].lower() or "connection" in result["message"].lower()

    def test_handle_error_custom_message(self, error_handler, logger):
        """Test providing custom user message"""
        error = RuntimeError("Technical error")
        custom_msg = "Please try again later"

        result = error_handler.handle_error(
            error,
            user_message=custom_msg
        )

        assert result["message"] == custom_msg

    def test_handle_error_severity_levels(self, error_handler, logger):
        """Test different severity levels"""
        error = RuntimeError("Test")

        for severity in ErrorSeverity:
            result = error_handler.handle_error(error, severity=severity)
            assert result["severity"] == severity.value

    def test_wrap_async_function(self, error_handler):
        """Test wrapping async functions with error handling"""

        @error_handler.wrap_async
        async def test_func():
            raise ValueError("Test error")

        with pytest.raises(ErrorWithContext):
            asyncio.run(test_func())

    def test_wrap_sync_function(self, error_handler):
        """Test wrapping sync functions with error handling"""

        @error_handler.wrap_sync
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ErrorWithContext):
            test_func()


class TestErrorWithContext:
    """Test ErrorWithContext exception"""

    def test_error_with_context_init(self):
        """Test ErrorWithContext initialization"""
        error_info = {
            "error_code": "test_error",
            "message": "Test message",
            "severity": "error"
        }

        exc = ErrorWithContext(error_info)
        assert exc.error_info == error_info
        assert str(exc) == "Test message"

    def test_error_with_context_full_info(self):
        """Test accessing full error info"""
        error_info = {
            "error_code": "api_timeout",
            "category": "api",
            "severity": "error",
            "message": "Request timed out",
            "context": {"service": "openai"}
        }

        exc = ErrorWithContext(error_info)
        assert exc.error_info["category"] == "api"
        assert exc.error_info["context"]["service"] == "openai"


class TestHealthChecker:
    """Test HealthChecker functionality"""

    @pytest.fixture
    def logger(self):
        """Create mock logger"""
        return Mock(spec=StructuredLogger)

    @pytest.fixture
    def health_checker(self, logger):
        """Create health checker instance"""
        return HealthChecker(logger)

    @pytest.mark.asyncio
    async def test_check_all(self, health_checker):
        """Test running all health checks"""
        with patch.object(health_checker, 'check_database', new_callable=AsyncMock) as mock_db:
            with patch.object(health_checker, 'check_disk_space', new_callable=AsyncMock) as mock_disk:
                with patch.object(health_checker, 'check_memory', new_callable=AsyncMock) as mock_mem:
                    with patch.object(health_checker, 'check_api_connectivity', new_callable=AsyncMock) as mock_api:
                        with patch.object(health_checker, 'check_plugins', new_callable=AsyncMock) as mock_plugins:
                            mock_db.return_value = {"status": "healthy"}
                            mock_disk.return_value = {"status": "healthy"}
                            mock_mem.return_value = {"status": "healthy"}
                            mock_api.return_value = {"status": "healthy"}
                            mock_plugins.return_value = {"status": "healthy"}

                            result = await health_checker.check_all()

                            assert result["status"] == "healthy"
                            assert "checks" in result
                            assert "database" in result["checks"]
                            assert "disk_space" in result["checks"]
                            assert "memory" in result["checks"]

    @pytest.mark.asyncio
    async def test_check_all_unhealthy(self, health_checker):
        """Test health check with failures"""
        with patch.object(health_checker, 'check_database', new_callable=AsyncMock) as mock_db:
            with patch.object(health_checker, 'check_disk_space', new_callable=AsyncMock) as mock_disk:
                with patch.object(health_checker, 'check_memory', new_callable=AsyncMock) as mock_mem:
                    with patch.object(health_checker, 'check_api_connectivity', new_callable=AsyncMock) as mock_api:
                        with patch.object(health_checker, 'check_plugins', new_callable=AsyncMock) as mock_plugins:
                            mock_db.return_value = {"status": "unhealthy"}
                            mock_disk.return_value = {"status": "unhealthy"}
                            mock_mem.return_value = {"status": "unhealthy"}
                            mock_api.return_value = {"status": "unhealthy"}
                            mock_plugins.return_value = {"status": "unhealthy"}

                            result = await health_checker.check_all()

                            assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_disk_space_healthy(self, health_checker):
        """Test disk space check with sufficient space"""
        mock_stat = Mock()
        mock_stat.free = 10 * (1024**3)  # 10 GB

        with patch('shutil.disk_usage', return_value=mock_stat):
            result = await health_checker.check_disk_space()
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_disk_space_warning(self, health_checker):
        """Test disk space check with low space"""
        mock_stat = Mock()
        mock_stat.free = 3 * (1024**3)  # 3 GB

        with patch('shutil.disk_usage', return_value=mock_stat):
            result = await health_checker.check_disk_space()
            assert result["status"] == "warning"

    @pytest.mark.asyncio
    async def test_check_disk_space_unhealthy(self, health_checker):
        """Test disk space check with very low space"""
        mock_stat = Mock()
        mock_stat.free = 0.5 * (1024**3)  # 0.5 GB

        with patch('shutil.disk_usage', return_value=mock_stat):
            result = await health_checker.check_disk_space()
            assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_memory_healthy(self, health_checker):
        """Test memory check with normal usage"""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value.available = 8 * (1024**3)
            mock_mem.return_value.percent = 60

            result = await health_checker.check_memory()
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_memory_warning(self, health_checker):
        """Test memory check with high usage"""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value.available = 2 * (1024**3)
            mock_mem.return_value.percent = 85

            result = await health_checker.check_memory()
            assert result["status"] == "warning"

    @pytest.mark.asyncio
    async def test_check_memory_unhealthy(self, health_checker):
        """Test memory check with very high usage"""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value.available = 0.5 * (1024**3)
            mock_mem.return_value.percent = 95

            result = await health_checker.check_memory()
            assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_memory_no_psutil(self, health_checker):
        """Test memory check without psutil installed"""
        with patch('psutil.virtual_memory', side_effect=ImportError):
            result = await health_checker.check_memory()
            assert result["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_check_plugins_healthy(self, health_checker):
        """Test plugins check with plugins directory"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.glob', return_value=[Mock(), Mock()]):
                result = await health_checker.check_plugins()
                assert result["status"] == "healthy"
                assert "plugins installed" in result["message"]

    @pytest.mark.asyncio
    async def test_check_plugins_missing_dir(self, health_checker):
        """Test plugins check with missing directory"""
        with patch('pathlib.Path.exists', return_value=False):
            result = await health_checker.check_plugins()
            assert result["status"] == "warning"


class TestGetLogger:
    """Test get_logger factory function"""

    def test_get_logger_creates_new(self):
        """Test creating a new logger"""
        with patch('pathlib.Path.mkdir'):
            logger = get_logger("test_logger")
            assert logger.name == "test_logger"

    def test_get_logger_returns_cached(self):
        """Test that get_logger returns cached instance"""
        with patch('pathlib.Path.mkdir'):
            logger1 = get_logger("cached_logger")
            logger2 = get_logger("cached_logger")
            assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names create different loggers"""
        with patch('pathlib.Path.mkdir'):
            logger1 = get_logger("logger1")
            logger2 = get_logger("logger2")
            assert logger1 is not logger2
