"""Sliver service - delegates to SliverClient for session management."""
import logging
import os
from typing import List

from app.core.config import settings
from app.schemas.sliver import (
    SliverSession,
    CommandResponse,
    ImplantGenerateResponse,
)
from app.utils.sliver_client import SliverClient

logger = logging.getLogger(__name__)


class SliverService:
    """Sliver service using SliverClient (simulation or real gRPC)."""

    def _get_client(self) -> SliverClient:
        """Create a new SliverClient instance from current settings."""
        return SliverClient(
            host=settings.SLIVER_HOST,
            port=settings.SLIVER_PORT,
            enabled=settings.SLIVER_GRPC_ENABLED,
            config_path=settings.SLIVER_CONFIG_PATH or None,
            client_bin=os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "sliver-client.exe",
            ),
        )

    async def get_sessions(self) -> List[SliverSession]:
        """Get all Sliver sessions.

        Returns:
            List of SliverSession objects.
        """
        client = self._get_client()
        sessions = client.get_sessions()

        result = []
        for s in sessions:
            result.append(SliverSession(
                id=s.get("id", ""),
                host=s.get("host", ""),
                user=s.get("user", ""),
                platform=s.get("platform", "unknown"),
                created_at=s.get("created_at"),
                last_seen=s.get("last_seen"),
                status=s.get("status", "active"),
            ))
        return result

    async def delete_session(self, session_id: str) -> bool:
        """Delete a Sliver session.

        Args:
            session_id: Session ID to delete.

        Returns:
            True if successful, False otherwise.
        """
        client = self._get_client()
        result = client.delete_session(session_id)
        logger.info("Delete session %s: %s", session_id, result)
        return result.get("success", False)

    async def execute_command(self, session_id: str, command: str) -> CommandResponse:
        """Execute a command on a Sliver session.

        Args:
            session_id: Target session ID.
            command: Command to execute.

        Returns:
            CommandResponse with output.
        """
        client = self._get_client()
        result = client.execute_command(session_id, command)
        return CommandResponse(output=result.get("output", ""))

    async def generate_implant(self, params: dict) -> ImplantGenerateResponse:
        """Generate a new Sliver implant.

        Args:
            params: Implant generation parameters (lhost, lport, platform, format, etc.)

        Returns:
            ImplantGenerateResponse with message and download URL.
        """
        client = self._get_client()
        result = client.generate_implant(params)
        return ImplantGenerateResponse(
            message=result.get("message", "Implant generated"),
            session_id=result.get("session_id"),
            download_url=result.get("download_url"),
        )


# Singleton instance
sliver_service = SliverService()
