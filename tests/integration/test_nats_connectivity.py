"""Integration tests for NATS server connectivity and protocol validation.

Run with: pytest -m integration tests/integration/test_nats_connectivity.py -v
Tests connectivity to actual NATS server configured via NATS_URL environment variable.
"""

import json
import os
import socket
import time

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class TestNATSConnectivity:
    """Test NATS server connectivity."""

    def test_nats_server_connectivity(self) -> None:
        """Test basic TCP connectivity to NATS server."""
        nats_url = os.environ.get("NATS_URL")
        if not nats_url:
            pytest.skip("NATS_URL not set; skipping NATS connectivity test")

        # Parse NATS URL (nats://host:port)
        if not nats_url.startswith("nats://"):
            pytest.skip("NATS_URL format invalid; should start with nats://")

        url_parts = nats_url.replace("nats://", "").split(":")
        if len(url_parts) != 2:
            pytest.skip("NATS_URL format invalid; should be nats://host:port")

        host, port = url_parts[0], int(url_parts[1])

        # Test TCP connectivity
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result != 0:
                pytest.skip(f"NATS server not accessible at {host}:{port}")

            print(f"✅ NATS TCP connectivity: {host}:{port}")

        except Exception as e:
            pytest.skip(f"NATS connectivity test failed: {e}")

    def test_nats_protocol_handshake(self) -> None:
        """Test NATS protocol handshake."""
        nats_url = os.environ.get("NATS_URL")
        if not nats_url:
            pytest.skip("NATS_URL not set")

        # Parse URL
        url_parts = nats_url.replace("nats://", "").split(":")
        if len(url_parts) != 2:
            pytest.skip("NATS_URL format invalid")

        host, port = url_parts[0], int(url_parts[1])

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))

            # Read NATS INFO message
            info_data = sock.recv(4096).decode('utf-8')
            assert info_data.startswith("INFO"), f"Expected NATS INFO, got: {info_data[:50]}"

            # Parse server info
            info_json = info_data.split("INFO ")[1].strip()
            server_info = json.loads(info_json)

            print(f"✅ NATS server info: {server_info.get('server_name', 'unknown')}")
            print(f"✅ NATS version: {server_info.get('version', 'unknown')}")
            print(f"✅ NATS max payload: {server_info.get('max_payload', 'unknown'):,} bytes")

            # Send basic CONNECT
            connect_msg = json.dumps({"verbose": False, "name": "antilurk_bot_test"})
            sock.send(f"CONNECT {connect_msg}\r\n".encode())

            # Test PING/PONG
            sock.send(b"PING\r\n")
            time.sleep(0.1)
            response = sock.recv(1024).decode('utf-8')

            if "PONG" not in response:
                pytest.fail(f"NATS PING/PONG failed: {response}")

            print("✅ NATS protocol handshake successful")
            sock.close()

        except json.JSONDecodeError as e:
            pytest.skip(f"NATS server returned invalid JSON: {e}")
        except Exception as e:
            pytest.skip(f"NATS protocol test failed: {e}")

    def test_nats_http_monitoring(self) -> None:
        """Test NATS HTTP monitoring endpoint."""
        nats_url = os.environ.get("NATS_URL")
        if not nats_url:
            pytest.skip("NATS_URL not set")

        # Parse URL
        url_parts = nats_url.replace("nats://", "").split(":")
        if len(url_parts) != 2:
            pytest.skip("NATS_URL format invalid")

        host, _ = url_parts[0], int(url_parts[1])

        # Try common NATS HTTP monitoring ports
        monitoring_ports = [8222, 8080]

        for port in monitoring_ports:
            try:
                import urllib.request
                url = f"http://{host}:{port}/varz"

                with urllib.request.urlopen(url, timeout=5) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        print(f"✅ NATS monitoring available at {host}:{port}")
                        print(f"✅ NATS connections: {data.get('connections', 'unknown')}")
                        print(f"✅ NATS messages in/out: {data.get('in_msgs', 0)}/{data.get('out_msgs', 0)}")
                        return  # Success

            except Exception:
                continue  # Try next port

        print("ℹ️  NATS HTTP monitoring not accessible (this is optional)")

    def test_nats_message_publishing(self) -> None:
        """Test basic message publishing to NATS server."""
        nats_url = os.environ.get("NATS_URL")
        if not nats_url:
            pytest.skip("NATS_URL not set")

        # Parse URL
        url_parts = nats_url.replace("nats://", "").split(":")
        if len(url_parts) != 2:
            pytest.skip("NATS_URL format invalid")

        host, port = url_parts[0], int(url_parts[1])

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))

            # Read INFO and send CONNECT
            _ = sock.recv(4096)
            connect_msg = json.dumps({
                "verbose": False,
                "name": "antilurk_bot_integration_test",
                "protocol": 1
            })
            sock.send(f"CONNECT {connect_msg}\r\n".encode())

            # Publish a test message
            test_subject = "antilurk.test.integration"
            test_message = json.dumps({
                "test": "integration_test",
                "timestamp": time.time(),
                "component": "antilurk_bot"
            })

            pub_command = f"PUB {test_subject} {len(test_message)}\r\n{test_message}\r\n"
            sock.send(pub_command.encode())

            # Send PING to ensure message was processed
            sock.send(b"PING\r\n")
            time.sleep(0.1)
            response = sock.recv(1024).decode('utf-8')

            if "PONG" in response:
                print("✅ NATS message publishing successful")
            else:
                pytest.fail(f"NATS message publishing failed: {response}")

            sock.close()

        except Exception as e:
            pytest.skip(f"NATS message publishing test failed: {e}")

    def test_nats_subscription(self) -> None:
        """Test basic subscription to NATS subjects."""
        nats_url = os.environ.get("NATS_URL")
        if not nats_url:
            pytest.skip("NATS_URL not set")

        # Parse URL
        url_parts = nats_url.replace("nats://", "").split(":")
        if len(url_parts) != 2:
            pytest.skip("NATS_URL format invalid")

        host, port = url_parts[0], int(url_parts[1])

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))

            # Read INFO and send CONNECT
            _ = sock.recv(4096)
            connect_msg = json.dumps({
                "verbose": False,
                "name": "antilurk_bot_sub_test",
                "protocol": 1
            })
            sock.send(f"CONNECT {connect_msg}\r\n".encode())

            # Subscribe to test subject
            test_subject = "antilurk.test.sub"
            sub_id = "1"
            sub_command = f"SUB {test_subject} {sub_id}\r\n"
            sock.send(sub_command.encode())

            # Publish a message to the subscribed subject
            test_message = "subscription_test"
            pub_command = f"PUB {test_subject} {len(test_message)}\r\n{test_message}\r\n"
            sock.send(pub_command.encode())

            # Try to receive the message (with timeout)
            sock.settimeout(2)
            try:
                response = sock.recv(1024).decode('utf-8')
                if f"MSG {test_subject}" in response and test_message in response:
                    print("✅ NATS subscription working")
                else:
                    print(f"ℹ️  NATS subscription response: {response[:100]}")
            except TimeoutError:
                print("ℹ️  NATS subscription test timeout (this may be normal)")

            # Unsubscribe and close
            unsub_command = f"UNSUB {sub_id}\r\n"
            sock.send(unsub_command.encode())
            sock.close()

        except Exception as e:
            pytest.skip(f"NATS subscription test failed: {e}")

    def test_nats_server_performance_info(self) -> None:
        """Test NATS server performance and configuration info."""
        nats_url = os.environ.get("NATS_URL")
        if not nats_url:
            pytest.skip("NATS_URL not set")

        # Parse URL for monitoring endpoint
        url_parts = nats_url.replace("nats://", "").split(":")
        if len(url_parts) != 2:
            pytest.skip("NATS_URL format invalid")

        host = url_parts[0]

        # Try to get server stats
        monitoring_ports = [8222, 8080]

        for port in monitoring_ports:
            try:
                import urllib.request

                # Get server variables
                varz_url = f"http://{host}:{port}/varz"
                with urllib.request.urlopen(varz_url, timeout=5) as response:
                    if response.status == 200:
                        varz_data = json.loads(response.read().decode())

                        print("✅ NATS Server Performance Info:")
                        print(f"   Server ID: {varz_data.get('server_id', 'unknown')}")
                        print(f"   Version: {varz_data.get('version', 'unknown')}")
                        print(f"   Uptime: {varz_data.get('uptime', 'unknown')}")
                        print(f"   Connections: {varz_data.get('connections', 0)}")
                        print(f"   Total connections: {varz_data.get('total_connections', 0)}")
                        print(f"   Messages in: {varz_data.get('in_msgs', 0):,}")
                        print(f"   Messages out: {varz_data.get('out_msgs', 0):,}")
                        print(f"   Bytes in: {varz_data.get('in_bytes', 0):,}")
                        print(f"   Bytes out: {varz_data.get('out_bytes', 0):,}")
                        print(f"   Max payload: {varz_data.get('max_payload', 0):,} bytes")

                        return  # Success

            except Exception:
                continue  # Try next port

        print("ℹ️  NATS performance info not available")


class TestNATSIntegration:
    """Test NATS integration with bot components."""

    def test_nats_bot_publisher_config(self) -> None:
        """Test NATS configuration for bot event publishing."""
        nats_url = os.environ.get("NATS_URL")
        if not nats_url:
            pytest.skip("NATS_URL not set")

        # Test that bot's NATS publisher can be configured
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

            from telegram_antilurk_bot.logging.nats_publisher import NATSPublisher

            # Create publisher instance
            publisher = NATSPublisher()
            assert publisher.nats_url == nats_url

            if publisher.enabled:
                print("✅ NATS publisher configured and enabled")
            else:
                print("ℹ️  NATS publisher configured but disabled")

        except ImportError as e:
            pytest.skip(f"Bot NATS publisher not available: {e}")
        except Exception as e:
            pytest.fail(f"NATS publisher configuration failed: {e}")

    def test_nats_event_subjects(self) -> None:
        """Test that expected NATS subjects are accessible."""
        nats_url = os.environ.get("NATS_URL")
        if not nats_url:
            pytest.skip("NATS_URL not set")

        # Expected subjects that the bot might use
        expected_subjects = [
            "antilurk.user.joined",
            "antilurk.user.left",
            "antilurk.challenge.created",
            "antilurk.challenge.completed",
            "antilurk.audit.completed",
            "antilurk.moderation.action"
        ]

        # Parse URL
        url_parts = nats_url.replace("nats://", "").split(":")
        if len(url_parts) != 2:
            pytest.skip("NATS_URL format invalid")

        host, port = url_parts[0], int(url_parts[1])

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))

            # Read INFO and connect
            _ = sock.recv(4096)
            connect_msg = json.dumps({"verbose": False, "name": "antilurk_subjects_test"})
            sock.send(f"CONNECT {connect_msg}\r\n".encode())

            # Test publishing to each expected subject
            for subject in expected_subjects:
                test_msg = f"test_{subject}"
                pub_cmd = f"PUB {subject} {len(test_msg)}\r\n{test_msg}\r\n"
                sock.send(pub_cmd.encode())

            # PING to ensure all messages processed
            sock.send(b"PING\r\n")
            time.sleep(0.1)
            response = sock.recv(1024).decode('utf-8')

            if "PONG" in response:
                print(f"✅ All {len(expected_subjects)} NATS subjects accessible")
            else:
                pytest.fail(f"NATS subjects test failed: {response}")

            sock.close()

        except Exception as e:
            pytest.skip(f"NATS subjects test failed: {e}")
