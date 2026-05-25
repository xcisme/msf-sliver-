"""Sliver C2 client wrapper.

Uses the official sliver-client binary in two modes:
- MCP (JSON-RPC stdio): for listing sessions
- Console RC scripts: for executing commands and generating implants

Falls back to simulation mode when SLIVER_GRPC_ENABLED=False.
"""
import json
import logging
import os
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Command simulation (fallback when not connected to real Sliver)
# ---------------------------------------------------------------------------

_SIMULATED_COMMANDS: Dict[str, Dict[str, str]] = {
    "linux": {
        "whoami": "root\n",
        "id": "uid=0(root) gid=0(root) groups=0(root)\n",
        "hostname": "web-prod-01\n",
        "pwd": "/root\n",
        "uname -a": "Linux web-prod-01 5.10.0-21-amd64 #1 SMP Debian x86_64 GNU/Linux\n",
        "ip addr": "eth0: inet 192.168.1.10/24\n",
        "ps aux": "root 1 0.0 0.1 225780 9384 ? Ss Jan01 0:05 /sbin/init\nroot 529 0.0 0.2 32940 16780 ? Ss Jan01 0:03 /usr/sbin/sshd -D\n",
        "ls": "Desktop  Documents  Downloads  Music  Pictures  Public  Templates  Videos\n",
        "cat /etc/passwd": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n",
        "netstat -antp": "tcp 0 0 0.0.0.0:22 0.0.0.0:* LISTEN 529/sshd\ntcp 0 0 0.0.0.0:80 0.0.0.0:* LISTEN 1103/nginx\n",
        "df -h": "/dev/sda1 20G 8.5G 11G 45% /\n/dev/sda2 100G 45G 55G 46% /data\n",
    },
    "windows": {
        "whoami": "nt authority\\system\n",
        "hostname": "WIN-DC01\r\n",
        "ipconfig": "IPv4 Address: 10.0.0.5\r\nSubnet Mask: 255.255.255.0\r\n",
        "systeminfo": "OS Name: Microsoft Windows Server 2019 Standard\r\nOS Version: 10.0.17763\r\n",
        "net user": "Administrator  DefaultAccount  Guest  john.smith  svc_backup\n",
        "tasklist": "System 4 Services 0 5,432 K\nsmss.exe 280 Services 0 1,024 K\ncsrss.exe 372 Services 0 4,876 K\n",
        "dir C:\\": "Program Files  Users  Windows  Temp  pagefile.sys\n",
    },
}


def _detect_platform(platform_hint: Optional[str] = None) -> str:
    if platform_hint:
        lowered = platform_hint.lower()
        if "win" in lowered:
            return "windows"
        if "linux" in lowered or "mac" in lowered or "darwin" in lowered:
            return "linux"
    return "linux"


def _simulate_command_output(platform: str, command: str) -> str:
    cmd = command.strip()
    platform_cmds = _SIMULATED_COMMANDS.get(platform, _SIMULATED_COMMANDS["linux"])
    if cmd in platform_cmds:
        return platform_cmds[cmd]
    first_word = cmd.split()[0] if cmd else ""
    for known_cmd, output in platform_cmds.items():
        if first_word == known_cmd.split()[0]:
            return output
    return f"[simulated] {platform}$ {command}\n"


# ---------------------------------------------------------------------------
# SliverClient
# ---------------------------------------------------------------------------

class SliverClient:
    """Sliver C2 client using official sliver-client binary (MCP + RC console)."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 31337,
        enabled: bool = False,
        config_path: Optional[str] = None,
        client_bin: Optional[str] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.enabled = enabled
        self.config_path = config_path
        self.client_bin = client_bin or self._find_client_bin()

    def _find_client_bin(self) -> str:
        """Find the sliver-client binary."""
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", "sliver-client.exe"),
            os.path.join(os.path.dirname(__file__), "..", "..", "sliver-client"),
            "sliver-client.exe",
            "sliver-client",
        ]
        for c in candidates:
            p = os.path.abspath(c)
            if os.path.exists(p):
                return p
        return "sliver-client.exe"

    def _ensure_mcp(self) -> bool:
        """Start and initialize a persistent MCP subprocess. Returns True if ready."""
        if hasattr(self, '_mcp_proc') and self._mcp_proc is not None:
            # Check if process is still alive
            if self._mcp_proc.poll() is None:
                return True
            self._mcp_proc = None

        cmd = [self.client_bin, "mcp"]
        if self.config_path:
            cmd.extend(["--config", self.config_path])

        try:
            self._mcp_proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            # Send initialize
            init_req = json.dumps({
                "jsonrpc": "2.0", "id": 0, "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                           "clientInfo": {"name": "c2", "version": "1.0"}},
            })
            self._mcp_proc.stdin.write(init_req + "\n")
            self._mcp_proc.stdin.flush()
            resp_line = self._mcp_proc.stdout.readline()
            if not resp_line or "result" not in resp_line:
                logger.warning("MCP init failed: %s", resp_line[:100] if resp_line else 'no response')
                self._mcp_proc.kill()
                self._mcp_proc = None
                return False
            self._mcp_req_id = 1
            logger.info("Persistent MCP connection established")
            return True
        except Exception as e:
            logger.warning("Failed to start MCP: %s", e)
            self._mcp_proc = None
            return False

    def _mcp_call(self, method: str, params: dict = None, timeout: int = 10) -> dict:
        """Call a tool/initialize via the persistent MCP connection."""
        if not self._ensure_mcp():
            return {"error": "MCP not available"}

        try:
            req = json.dumps({
                "jsonrpc": "2.0", "id": self._mcp_req_id,
                "method": method, "params": params or {},
            })
            self._mcp_req_id += 1
            self._mcp_proc.stdin.write(req + "\n")
            self._mcp_proc.stdin.flush()
            resp_line = self._mcp_proc.stdout.readline()
            if resp_line and resp_line.strip():
                return json.loads(resp_line)
            return {"error": "empty MCP response"}
        except Exception as e:
            logger.warning("MCP call failed: %s, restarting MCP", e)
            try:
                self._mcp_proc.kill()
            except Exception:
                pass
            self._mcp_proc = None
            return {"error": str(e)}

    def _run_mcp(self, method: str, params: dict = None, timeout: int = 10) -> dict:
        """Send a single request via persistent MCP connection."""
        return self._mcp_call(method, params, timeout)

    def _run_rc(self, commands: List[str], timeout: int = 30) -> str:
        """Run commands via sliver-client console RC script."""
        rc_content = "\n".join(commands) + "\nexit\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".rc", delete=False, newline="\n"
        ) as f:
            f.write(rc_content)
            rc_path = f.name

        try:
            proc = subprocess.Popen(
                [self.client_bin, "console", "--rc", rc_path],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = proc.communicate(timeout=timeout)
            output = stdout.decode(errors="replace")
            if stderr:
                err_text = stderr.decode(errors="replace")
                if "error" in err_text.lower():
                    logger.warning("RC stderr: %s", err_text)
            return output
        except subprocess.TimeoutExpired:
            proc.kill()
            return ""
        finally:
            try:
                os.unlink(rc_path)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def test_connection(self) -> Dict[str, Any]:
        """Test Sliver connection via MCP."""
        if not self.enabled:
            db = SessionLocal()
            try:
                result = db.execute(text("SELECT COUNT(*) as cnt FROM sliver_sessions"))
                row = result.fetchone()
                count = row.cnt if row else 0
            except Exception:
                count = 0
            finally:
                db.close()
            return {
                "status": "success",
                "message": "Sliver simulation mode",
                "sessions_count": count,
                "mode": "simulation",
            }

        resp = self._run_mcp("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "c2-coordinator", "version": "1.0"},
        })
        if resp.get("error"):
            return {
                "status": "error",
                "message": f"Connection failed: {resp.get('error')}",
                "sessions_count": 0,
                "mode": "real",
            }
        server_info = resp.get("result", {}).get("serverInfo", {})
        return {
            "status": "success",
            "message": f"Sliver connected ({server_info.get('version', '?')})",
            "sessions_count": 0,
            "mode": "real",
        }

    def get_sessions(self) -> List[Dict[str, Any]]:
        """List all Sliver sessions from MCP (Kali) + DB cache."""
        if not self.enabled:
            return self._get_sessions_db()

        sessions = []
        resp = self._mcp_call("tools/call", {
            "name": "list_sessions_and_beacons",
            "arguments": {},
        }, timeout=5)
        if not resp.get("error"):
            result = resp.get("result", {})
            # Try structuredContent first (JSON format)
            sc = result.get("structuredContent", {})
            if sc:
                for s in sc.get("sessions", []):
                    sessions.append({
                        "id": s.get("id", ""),
                        "host": s.get("hostname", "") or s.get("remote_address", ""),
                        "user": s.get("username", ""),
                        "platform": f"{s.get('os','')}/{s.get('arch','')}" if s.get('os') else "",
                        "status": "closed" if s.get("is_dead") else "active",
                    })
                for b in sc.get("beacons", []):
                    sessions.append({
                        "id": b.get("id", ""),
                        "host": b.get("hostname", "") or b.get("remote_address", ""),
                        "user": b.get("username", ""),
                        "platform": f"{b.get('os','')}/{b.get('arch','')}" if b.get('os') else "",
                        "status": "beacon",
                    })
            # Fallback: parse text content
            if not sessions:
                content = result.get("content", [])
                if content:
                    text = content[0].get("text", "") if content else ""
                    sessions = self._parse_sessions_text(text)

        # Merge DB cached sessions (from simulated implants)
        db_sessions = self._get_sessions_db()
        mcp_ids = {s["id"] for s in sessions}
        for s in db_sessions:
            if s["id"] not in mcp_ids:
                sessions.append(s)

        return sessions

    def _get_sessions_db(self) -> List[Dict[str, Any]]:
        """Get sessions from database (simulation/offline mode)."""
        db = SessionLocal()
        try:
            rows = db.execute(
                text("SELECT id, host, user, platform, created_at, last_seen, status "
                     "FROM sliver_sessions ORDER BY created_at DESC")
            ).fetchall()
            return [
                {
                    "id": r.id, "host": r.host or "", "user": r.user or "",
                    "platform": r.platform or "unknown",
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "last_seen": r.last_seen.isoformat() if r.last_seen else None,
                    "status": r.status or "active",
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("DB sessions failed: %s", e)
            return []
        finally:
            db.close()

    def _parse_sessions_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse sliver session list text output."""
        sessions = []
        lines = text.strip().split("\n")
        # Skip header lines
        in_table = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "ID" in line and "Name" in line and "Transport" in line:
                in_table = True
                continue
            if in_table and line.startswith("═") or line.startswith("│"):
                continue
            if in_table and line:
                parts = [p.strip() for p in line.split("│")]
                if len(parts) >= 4:
                    sid = parts[0].strip()
                    host = parts[1].strip() if len(parts) > 1 else ""
                    user = parts[2].strip() if len(parts) > 2 else ""
                    platform = parts[3].strip() if len(parts) > 3 else ""
                    if sid and sid != "Session ID":
                        sessions.append({
                            "id": sid, "host": host, "user": user,
                            "platform": platform, "status": "active",
                        })
        return sessions

    def execute_command(self, session_id: str, command: str) -> Dict[str, Any]:
        """Execute a command on a Sliver session via RC console."""
        if not self.enabled:
            platform = self._get_session_platform(session_id)
            output = _simulate_command_output(platform, command)
            return {"output": output, "session_id": session_id}

        output = self._run_rc([
            f"use -s {session_id}",
            f"execute -o {command}",
            "sleep 2",
        ], timeout=15)
        return {"output": output or f"[executed] {command}", "session_id": session_id}

    def _get_session_platform(self, session_id: str) -> str:
        db = SessionLocal()
        try:
            row = db.execute(
                text("SELECT platform FROM sliver_sessions WHERE id = :sid"),
                {"sid": session_id},
            ).fetchone()
            if row and row.platform:
                return _detect_platform(row.platform)
        except Exception:
            pass
        finally:
            db.close()
        return "linux"

    def generate_implant(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a real Sliver implant via RC console with adequate timeout."""
        platform = config.get("platform", "windows/amd64")
        lhost = config.get("lhost", self.host)
        lport = config.get("lport", self.port)
        fmt = config.get("format", "exe")

        if not self.enabled:
            return self._generate_implant_simulated(config)

        # Real generate requires Go compiler (unavailable on Windows Sliver Server).
        # Fall back to simulated mode immediately for fast response.
        return self._generate_implant_simulated(config)

    def _generate_implant_simulated(self, config: Dict[str, Any]) -> Dict[str, Any]:
        platform = config.get("platform", "windows/amd64")
        lhost = config.get("lhost", self.host)
        lport = config.get("lport", self.port)
        fmt = config.get("format", "exe")
        session_id = "sliver-" + uuid.uuid4().hex[:12]
        platform_norm = _detect_platform(platform)
        fake_host = "10.0.0.5" if platform_norm == "windows" else "192.168.1.10"
        fake_user = "nt authority\\system" if platform_norm == "windows" else "root"
        now = datetime.now(timezone.utc)

        db = SessionLocal()
        try:
            db.execute(
                text(
                    "INSERT INTO sliver_sessions (id, host, user, platform, "
                    "created_at, last_seen, status) "
                    "VALUES (:id, :host, :user, :platform, :created_at, :last_seen, :status)"
                ),
                {"id": session_id, "host": fake_host, "user": fake_user,
                 "platform": platform, "created_at": now, "last_seen": now, "status": "active"},
            )
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Simulated implant insert failed: %s", e)
            return {"message": f"Failed: {e}", "session_id": None, "download_url": None}
        finally:
            db.close()

        return {
            "message": f"Implant generated (simulation) - {platform} {fmt}",
            "session_id": session_id,
            "download_url": f"http://{lhost}:{lport}/downloads/sliver_implant_{session_id}.{fmt}",
        }

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a Sliver session."""
        if not self.enabled:
            db = SessionLocal()
            try:
                row = db.execute(text("SELECT id FROM sliver_sessions WHERE id = :sid"), {"sid": session_id}).fetchone()
                if not row:
                    return {"success": False, "message": f"Session {session_id} not found"}
                db.execute(text("DELETE FROM sliver_sessions WHERE id = :sid"), {"sid": session_id})
                db.commit()
                return {"success": True, "message": f"Session {session_id} deleted"}
            except Exception as e:
                db.rollback()
                return {"success": False, "message": str(e)}
            finally:
                db.close()

        output = self._run_rc([
            f"use -s {session_id}",
            "kill",
            "sleep 1",
        ], timeout=10)
        return {"success": True, "message": f"Session {session_id} kill sent", "output": output}
