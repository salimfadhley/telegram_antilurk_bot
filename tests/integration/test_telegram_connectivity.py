"""Integration tests for Telegram Bot API connectivity and validation.

Run with: pytest -m integration tests/integration/test_telegram_connectivity.py -v
Tests connectivity to actual Telegram Bot API using TELEGRAM_TOKEN environment variable.
"""

import os

import aiohttp
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class TestTelegramBotAPI:
    """Test Telegram Bot API connectivity and token validation."""

    @pytest.mark.asyncio
    async def test_telegram_bot_token_validation(self) -> None:
        """Test Telegram bot token by calling getMe API."""
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            pytest.fail("TELEGRAM_TOKEN not set - required for integration tests")

        if "test" in token.lower() or len(token) < 30:
            pytest.fail("TELEGRAM_TOKEN appears to be a test token - use real bot token")

        url = f"https://api.telegram.org/bot{token}/getMe"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 401:
                    pytest.fail("Telegram bot token is invalid (401 Unauthorized)")
                elif response.status == 404:
                    pytest.fail("Telegram bot token format is incorrect (404 Not Found)")
                elif response.status != 200:
                    pytest.fail(f"Telegram API returned status {response.status}")

                data = await response.json()

                if not data.get("ok"):
                    pytest.fail(f"Telegram API error: {data.get('description', 'Unknown error')}")

                bot_info = data.get("result", {})
                assert bot_info.get("id"), "Bot ID missing from response"
                assert bot_info.get("first_name"), "Bot name missing from response"
                assert bot_info.get("username"), "Bot username missing from response"

                print(f"✅ Bot name: {bot_info.get('first_name')}")
                print(f"✅ Bot username: @{bot_info.get('username')}")
                print(f"✅ Bot ID: {bot_info.get('id')}")
                print(f"✅ Can join groups: {bot_info.get('can_join_groups', False)}")
                print(f"✅ Can read all messages: {bot_info.get('can_read_all_group_messages', False)}")
                print(f"✅ Supports inline queries: {bot_info.get('supports_inline_queries', False)}")

    @pytest.mark.asyncio
    async def test_telegram_webhook_info(self) -> None:
        """Test getting webhook information."""
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            pytest.fail("TELEGRAM_TOKEN not set - required for integration tests")

        if "test" in token.lower() or len(token) < 30:
            pytest.skip("Using test token - webhook info test not applicable")

        url = f"https://api.telegram.org/bot{token}/getWebhookInfo"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    pytest.fail(f"Telegram webhook API returned status {response.status}")

                data = await response.json()

                if not data.get("ok"):
                    pytest.fail(f"Telegram webhook API error: {data.get('description', 'Unknown error')}")

                webhook_info = data.get("result", {})
                webhook_url = webhook_info.get("url", "")

                if webhook_url:
                    print(f"ℹ️  Webhook URL: {webhook_url}")
                    print(f"ℹ️  Pending updates: {webhook_info.get('pending_update_count', 0)}")
                    print(f"ℹ️  Last error date: {webhook_info.get('last_error_date', 'None')}")
                    if webhook_info.get("last_error_message"):
                        print(f"ℹ️  Last error: {webhook_info.get('last_error_message')}")
                else:
                    print("ℹ️  No webhook configured (polling mode)")

                # Webhook info retrieved successfully regardless of configuration
                assert isinstance(webhook_info.get("pending_update_count", 0), int)

    @pytest.mark.asyncio
    async def test_telegram_bot_commands(self) -> None:
        """Test getting bot commands configuration."""
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            pytest.fail("TELEGRAM_TOKEN not set - required for integration tests")

        if "test" in token.lower() or len(token) < 30:
            pytest.skip("Using test token - commands test not applicable")

        url = f"https://api.telegram.org/bot{token}/getMyCommands"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    pytest.fail(f"Telegram commands API returned status {response.status}")

                data = await response.json()

                if not data.get("ok"):
                    pytest.fail(f"Telegram commands API error: {data.get('description', 'Unknown error')}")

                commands = data.get("result", [])
                print(f"✅ Bot commands configured: {len(commands)}")

                for cmd in commands:
                    print(f"   /{cmd.get('command', '')} - {cmd.get('description', '')}")

                # Commands list retrieved successfully (may be empty)
                assert isinstance(commands, list)

    @pytest.mark.asyncio
    async def test_telegram_api_rate_limiting(self) -> None:
        """Test Telegram API rate limiting behavior."""
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            pytest.fail("TELEGRAM_TOKEN not set - required for integration tests")

        if "test" in token.lower() or len(token) < 30:
            pytest.skip("Using test token - rate limiting test not applicable")

        url = f"https://api.telegram.org/bot{token}/getMe"

        # Make multiple rapid requests to test rate limiting
        async with aiohttp.ClientSession() as session:
            responses = []

            for i in range(3):  # Conservative test - just 3 requests
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    responses.append(response.status)

            # All requests should succeed (we're not hitting rate limits with just 3 requests)
            success_count = sum(1 for status in responses if status == 200)
            print(f"✅ Rate limiting test: {success_count}/3 requests successful")

            # At least the first request should succeed
            assert success_count >= 1, "At least one API request should succeed"

    @pytest.mark.asyncio
    async def test_telegram_bot_permissions(self) -> None:
        """Test bot's default permissions and capabilities."""
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            pytest.fail("TELEGRAM_TOKEN not set - required for integration tests")

        if "test" in token.lower() or len(token) < 30:
            pytest.skip("Using test token - permissions test not applicable")

        # Test getting bot info to check permissions
        url = f"https://api.telegram.org/bot{token}/getMe"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    pytest.fail(f"Failed to get bot info: status {response.status}")

                data = await response.json()
                bot_info = data.get("result", {})

                # Check critical permissions for anti-lurk bot functionality
                can_join_groups = bot_info.get("can_join_groups", False)
                can_read_all_messages = bot_info.get("can_read_all_group_messages", False)

                print("✅ Bot permissions check:")
                print(f"   Can join groups: {can_join_groups}")
                print(f"   Can read all group messages: {can_read_all_messages}")
                print(f"   Supports inline queries: {bot_info.get('supports_inline_queries', False)}")

                # For an anti-lurk bot, we need to be able to join groups
                assert can_join_groups, "Bot must be able to join groups for anti-lurk functionality"

                # Note: can_read_all_messages might be False if privacy mode is enabled
                if not can_read_all_messages:
                    print("ℹ️  Privacy mode may be enabled - bot will only see messages addressed to it")


class TestTelegramIntegration:
    """Test Telegram integration with bot components."""

    def test_telegram_bot_config_validation(self) -> None:
        """Test that Telegram bot is properly configured for the application."""
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            pytest.fail("TELEGRAM_TOKEN not set - required for integration tests")

        # Basic token format validation
        if not token.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
            pytest.fail("TELEGRAM_TOKEN doesn't start with valid bot ID")

        if ':' not in token:
            pytest.fail("TELEGRAM_TOKEN missing ':' separator")

        parts = token.split(':')
        if len(parts) != 2:
            pytest.fail("TELEGRAM_TOKEN should have exactly one ':' separator")

        bot_id, bot_token = parts

        # Bot ID should be numeric
        try:
            bot_id_int = int(bot_id)
            assert bot_id_int > 0, "Bot ID should be positive"
        except ValueError:
            pytest.fail("Bot ID portion of token should be numeric")

        # Bot token should be long enough
        assert len(bot_token) >= 35, "Bot token portion appears too short"

        print("✅ Token format validation passed")
        print(f"   Bot ID: {bot_id}")
        print(f"   Token length: {len(bot_token)} characters")

    @pytest.mark.asyncio
    async def test_telegram_error_handling(self) -> None:
        """Test proper error handling for invalid API calls."""
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            pytest.fail("TELEGRAM_TOKEN not set - required for integration tests")

        # Test with an invalid method
        url = f"https://api.telegram.org/bot{token}/invalidMethod"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                # Should return 404 for invalid method
                assert response.status == 404, "Invalid API method should return 404"

                data = await response.json()
                assert not data.get("ok"), "Invalid API call should have ok=false"
                assert "description" in data, "Error response should include description"

                print("✅ Error handling test passed")
                print(f"   Error description: {data.get('description', 'Unknown')}")

    @pytest.mark.asyncio
    async def test_telegram_api_connectivity_resilience(self) -> None:
        """Test API connectivity resilience and timeout handling."""
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            pytest.fail("TELEGRAM_TOKEN not set - required for integration tests")

        url = f"https://api.telegram.org/bot{token}/getMe"

        # Test with a very short timeout to ensure timeout handling works
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=0.001)) as response:
                    # This should timeout, but if it doesn't, that's also fine
                    data = await response.json()
                    print("✅ API call succeeded despite short timeout")
        except (aiohttp.ClientError, aiohttp.ServerTimeoutError, TimeoutError) as e:
            print(f"✅ Timeout handling working correctly: {type(e).__name__}")

        # Now test with reasonable timeout
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                assert response.status == 200, "API should be accessible with reasonable timeout"
                data = await response.json()
                assert data.get("ok"), "API response should be successful"
                print("✅ API connectivity resilient with proper timeout")
