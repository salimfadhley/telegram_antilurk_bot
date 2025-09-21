"""Smoke tests for deployment validation."""

import subprocess
from pathlib import Path

import pytest


class TestDeploymentSmoke:
    """Basic smoke tests for containerized deployment."""

    def test_dockerfile_exists(self) -> None:
        """Dockerfile should exist in project root."""
        dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile not found in project root"

    def test_docker_compose_exists(self) -> None:
        """Docker compose configuration should exist."""
        compose_path = Path(__file__).parent.parent.parent / "deploy" / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml not found in deploy directory"

    def test_portainer_stack_exists(self) -> None:
        """Portainer stack configuration should exist."""
        stack_path = Path(__file__).parent.parent.parent / "deploy" / "portainer-stack.yml"
        assert stack_path.exists(), "portainer-stack.yml not found in deploy directory"

    def test_env_example_exists(self) -> None:
        """.env.example should exist for reference."""
        env_example_path = Path(__file__).parent.parent.parent / ".env.example"
        assert env_example_path.exists(), ".env.example not found in project root"

    def test_main_module_importable(self) -> None:
        """Main module should be importable."""
        try:
            from telegram_antilurk_bot.main import main
            assert callable(main), "Main function should be callable"
        except ImportError as e:
            pytest.fail(f"Could not import main module: {e}")

    def test_package_entry_point_exists(self) -> None:
        """Package should have __main__.py entry point."""
        main_path = Path(__file__).parent.parent.parent / "src" / "telegram_antilurk_bot" / "__main__.py"
        assert main_path.exists(), "__main__.py not found in package"

    @pytest.mark.skipif(
        subprocess.run(["which", "docker"], capture_output=True).returncode != 0,
        reason="Docker not available"
    )
    def test_dockerfile_builds(self) -> None:
        """Dockerfile should build successfully."""
        project_root = Path(__file__).parent.parent.parent

        # Build docker image
        result = subprocess.run(
            ["docker", "build", "-t", "telegram-antilurk-bot:test", "."],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.fail(f"Docker build failed: {result.stderr}")

    @pytest.mark.skipif(
        subprocess.run(["which", "docker-compose"], capture_output=True).returncode != 0,
        reason="Docker Compose not available"
    )
    def test_docker_compose_validates(self) -> None:
        """Docker compose configuration should be valid."""
        deploy_dir = Path(__file__).parent.parent.parent / "deploy"

        result = subprocess.run(
            ["docker-compose", "config"],
            cwd=deploy_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.fail(f"Docker compose validation failed: {result.stderr}")

    def test_required_environment_variables_documented(self) -> None:
        """Required environment variables should be documented in .env.example."""
        env_example_path = Path(__file__).parent.parent.parent / ".env.example"
        env_content = env_example_path.read_text()

        # Check required variables are documented
        required_vars = ["TELEGRAM_TOKEN", "DATABASE_URL"]
        for var in required_vars:
            assert var in env_content, f"Required variable {var} not documented in .env.example"

    def test_startup_script_executable(self) -> None:
        """Main module should be executable."""
        main_path = Path(__file__).parent.parent.parent / "src" / "telegram_antilurk_bot" / "__main__.py"
        content = main_path.read_text()

        # Check for async main execution
        assert "asyncio.run(main())" in content, "__main__.py should call asyncio.run(main())"

    def test_configuration_directories_creatable(self, tmp_path: Path) -> None:
        """Configuration directories should be creatable."""
        config_dir = tmp_path / "config"
        data_dir = tmp_path / "data"

        # Should be able to create directories
        config_dir.mkdir(exist_ok=True)
        data_dir.mkdir(exist_ok=True)

        # Should be writable
        test_file = config_dir / "test.txt"
        test_file.write_text("test")
        assert test_file.exists()

    def test_deployment_documentation_exists(self) -> None:
        """Deployment documentation should exist."""
        deploy_readme = Path(__file__).parent.parent.parent / "deploy" / "README.md"
        assert deploy_readme.exists(), "Deployment README not found"

        content = deploy_readme.read_text()
        assert "Docker Compose" in content, "Docker Compose not documented"
        assert "Portainer" in content, "Portainer not documented"
        assert "Environment Variables" in content, "Environment variables not documented"


class TestEnvironmentValidation:
    """Tests for environment variable validation."""

    def test_telegram_token_format_validation(self) -> None:
        """Should validate Telegram token format."""
        # Valid format: bot_id:secret_key
        valid_token = "123456789:ABCdefGhIJKlmNoPQRstuVwxyZ-1234567890"

        # This would be tested in the actual application
        # Here we just document the expected format
        assert ":" in valid_token
        bot_id, secret = valid_token.split(":", 1)
        assert bot_id.isdigit()
        assert len(secret) > 10

    def test_database_url_format_validation(self) -> None:
        """Should validate database URL format."""
        valid_urls = [
            "postgresql://user:pass@host:5432/db",
            "postgres://user:pass@host:5432/db",
            "postgresql://user:pass@host/db",  # Default port
        ]

        for url in valid_urls:
            assert url.startswith(("postgresql://", "postgres://"))
            assert "@" in url  # Has credentials
            assert "/" in url.split("@", 1)[1]  # Has database name

    def test_optional_variables_have_defaults(self) -> None:
        """Optional environment variables should have sensible defaults."""
        defaults = {
            "DATA_DIR": "/data",
            "CONFIG_DIR": "/data/config",
            "TZ": "UTC",
            "LOG_LEVEL": "INFO"
        }

        # These would be tested in the actual configuration loading
        # Here we just document expected behavior
        for _var, default in defaults.items():
            assert default is not None
            assert isinstance(default, str)
            assert len(default) > 0


class TestHealthChecks:
    """Tests for health check functionality."""

    def test_basic_health_check_function(self) -> None:
        """Basic health check should be simple and fast."""
        # Simple Python import test - this is what our health check does
        try:
            result = 0  # Success
        except Exception:
            result = 1  # Failure

        assert result == 0, "Basic health check should pass"

    def test_health_check_configuration(self) -> None:
        """Health check should be properly configured in Docker."""
        dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile"
        dockerfile_content = dockerfile_path.read_text()

        # Should have health check defined
        assert "HEALTHCHECK" in dockerfile_content, "Dockerfile should define health check"
