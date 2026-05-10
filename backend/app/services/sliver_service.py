"""Sliver service for mock implementation."""
import logging
from datetime import datetime
from typing import List

from app.schemas.sliver import (
    SliverSession,
    CommandResponse,
    ImplantGenerateResponse
)

logger = logging.getLogger(__name__)


class SliverService:
    """Mock Sliver service for development."""

    async def get_sessions(self) -> List[SliverSession]:
        """Get Sliver sessions (mock data).

        Returns:
            List of mock Sliver sessions
        """
        now = datetime.now()
        return [
            SliverSession(
                id="abc123",
                host="192.168.1.10",
                user="root",
                platform="linux",
                created_at=now,
                last_seen=now,
                status="active"
            ),
            SliverSession(
                id="def456",
                host="10.0.0.5",
                user="admin",
                platform="windows",
                created_at=now,
                last_seen=now,
                status="active"
            )
        ]

    async def delete_session(self, session_id: str) -> bool:
        """Delete a Sliver session (mock).

        Args:
            session_id: Session ID to delete

        Returns:
            True if successful
        """
        logger.info(f"Mock delete session: {session_id}")
        return True

    async def execute_command(self, session_id: str, command: str) -> CommandResponse:
        """Execute command on a session (mock).

        Args:
            session_id: Target session ID
            command: Command to execute

        Returns:
            Command output
        """
        logger.info(f"Mock execute command on session {session_id}: {command}")

        # Simple mock commands
        if command == "whoami":
            output = "root\n"
        elif command == "pwd":
            output = "/root\n"
        elif command == "uname -a":
            output = "Linux target 5.10.0-21-amd64 #1 SMP Debian x86_64 GNU/Linux\n"
        elif command == "ip addr":
            output = "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000\n    inet 127.0.0.1/8 scope host lo\n       valid_lft forever preferred_lft forever\n"
        else:
            output = f"Mock output: You executed command '{command}'\n"

        return CommandResponse(output=output)

    async def generate_implant(self, params: dict) -> ImplantGenerateResponse:
        """Generate Sliver implant (mock).

        Args:
            params: Implant generation parameters

        Returns:
            Generation result with download URL
        """
        logger.info(f"Mock generate implant: {params}")

        return ImplantGenerateResponse(
            message="Implant generated (mock)",
            download_url=f"http://localhost:8000/downloads/sliver_implant_{params.get('lhost')}_{params.get('lport')}.exe"
        )


# Singleton instance
sliver_service = SliverService()