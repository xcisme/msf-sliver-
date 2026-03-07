"""Metasploit Framework RPC client wrapper."""
import logging
from typing import Any, Dict, List, Optional

from pymetasploit3.msfrpc import MsfRpcClient

logger = logging.getLogger(__name__)


class MsfClient:
    """Metasploit Framework RPC client wrapper."""

    def __init__(self, host: str, port: int, password: str, username: str = "msf") -> None:
        """Initialize MSF client.

        Args:
            host: MSF RPC server host
            port: MSF RPC server port
            password: MSF RPC password
            username: MSF RPC username (default: msf)
        """
        self.host = host
        self.port = port
        self.password = password
        self.username = username
        self._client: Optional[MsfRpcClient] = None

    def connect(self) -> MsfRpcClient:
        """Connect to MSF RPC server.

        Returns:
            MsfRpcClient instance

        Raises:
            Exception: If connection fails
        """
        try:
            self._client = MsfRpcClient(
                self.password,
                server=self.host,
                port=self.port
            )
            logger.info(f"Successfully connected to MSF RPC at {self.host}:{self.port}")
            return self._client
        except Exception as e:
            logger.error(f"Failed to connect to MSF RPC: {e}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """Test MSF connection status.

        Returns:
            Dictionary with connection status information
        """
        try:
            if self._client is None:
                self.connect()

            # Try to get exploits module list to verify connection
            exploits = self._client.modules.exploits
            sessions_count = len(self._client.sessions.list)

            return {
                "status": "success",
                "message": "MSF RPC connection successful",
                "sessions_count": sessions_count,
                "exploits_count": len(exploits)
            }
        except Exception as e:
            logger.error(f"MSF connection test failed: {e}")
            return {
                "status": "error",
                "message": f"MSF connection failed: {str(e)}",
                "sessions_count": 0
            }

    def get_sessions(self) -> List[Dict[str, Any]]:
        """Get current active sessions.

        Returns:
            List of session information dictionaries
        """
        try:
            if self._client is None:
                self.connect()

            sessions_list = self._client.sessions.list
            sessions = []

            for session_id, session_info in sessions_list.items():
                sessions.append({
                    "id": session_id,
                    "info": session_info
                })

            logger.info(f"Retrieved {len(sessions)} sessions")
            return sessions
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            raise

    def execute_exploit(self, module_path, options=None, payload=None) -> Dict[str, Any]:
        """
        执行exploit模块 - 严格遵循MSF的API规范

        MSF规范说明：
        - 对于需要payload的模块，payload必须在设置其他选项前单独设置
        - payload不是options字典的一部分，而是模块的一个属性
        - 格式：exploit['PAYLOAD'] = payload_name
        - multi/handler 特殊处理：LHOST, LPORT 属于 payload 选项，不是 exploit 选项

        :param module_path: exploit模块路径，如 'exploit/multi/handler'
        :param options: 模块选项字典，如 {"RHOSTS": "192.168.1.1", "RPORT": "445"}
        :param payload: payload名称，如 'windows/x64/meterpreter/reverse_tcp'
        :return: 执行结果字典
        """
        try:
            # 确保连接
            if self._client is None:
                self.connect()

            # 特殊处理 multi/handler 模块
            if module_path == 'exploit/multi/handler':
                logger.info("Detected multi/handler module, using special handling")
                return self._execute_handler(options, payload)
            else:
                # 常规 exploit 模块处理
                return self._execute_regular_exploit(module_path, options, payload)

        except Exception as e:
            logger.error(f"Failed to execute exploit {module_path}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Exploit execution failed: {str(e)}",
                "details": None
            }

    def _execute_handler(self, options=None, payload=None) -> Dict[str, Any]:
        """
        执行 multi/handler 模块

        multi/handler 的特殊性：
        - LHOST, LPORT 是 payload 的选项，不是 handler 的选项
        - 需要先创建 payload 模块并设置选项
        - 然后创建 handler 模块并执行

        :param options: 模块选项字典
        :param payload: payload名称
        :return: 执行结果字典
        """
        try:
            # 初始化 options 为空字典
            if options is None:
                options = {}

            # 获取 payload 名称（优先从 payload 参数，其次从 options['PAYLOAD']）
            payload_name = payload or options.get('PAYLOAD') or options.get('payload')

            if not payload_name:
                return {
                    "status": "error",
                    "message": "Payload is required for multi/handler module",
                    "details": None
                }

            logger.info(f"Creating payload module: {payload_name}")

            # 1. 创建 payload 模块
            payload_module = self._client.modules.use('payload', payload_name)

            # 2. 提取并设置 payload 的选项（LHOST, LPORT 等）
            payload_options = {}
            payload_option_keys = ['LHOST', 'LPORT', 'LPORTS', 'RHOST', 'RPORT',
                                   'AutoRunScript', 'InitialAutoRunScript',
                                   'AutoVerifySession', 'AutoVerifySessionTimeout',
                                   'ExitOnSession', 'ExitSessionTimeout',
                                   'HandlerRunAsJob', 'ListenerTimeout',
                                   'ListenerCommTimeout', 'EnableContextEncoding',
                                   'EnableUnicodeEncoding', 'StagerRetryCount',
                                   'StagerRetryWait', 'StagerFailNoRetry',
                                   'DisablePayloadHandler']

            # 从 options 中提取 payload 选项
            for key in payload_option_keys:
                if key in options:
                    payload_options[key] = options[key]

            # 设置 payload 选项
            logger.info(f"Setting payload options: {payload_options}")
            for key, value in payload_options.items():
                payload_module[key] = value

            # 3. 创建 multi/handler 模块
            logger.info("Creating multi/handler module")
            handler = self._client.modules.use('exploit', 'multi/handler')

            # 4. 提取 handler 的选项（排除 payload 选项和 PAYLOAD 本身）
            # 注意：payload 通过 execute(payload=payload_module) 传递，不需要设置 handler['Payload']
            handler_option_keys = ['ExitOnSession', 'VERBOSE', 'WORKSPACE', 'LHOST', 'LPORT']
            handler_options = {}
            
            for key, value in options.items():
                # 跳过 payload 专属选项和 PAYLOAD 键
                key_upper = key.upper()
                if key_upper in payload_option_keys:
                    logger.debug(f"Skipping payload option '{key}' for handler")
                    continue
                if key_upper == 'PAYLOAD':
                    logger.debug(f"Skipping PAYLOAD option for handler")
                    continue
                # 只设置 handler 支持的选项
                handler_options[key] = value

            # 设置 handler 选项
            if handler_options:
                logger.info(f"Setting handler options: {handler_options}")
                for key, value in handler_options.items():
                    try:
                        handler[key] = value
                        logger.debug(f"Set handler option '{key}' = {value}")
                    except Exception as opt_err:
                        logger.warning(f"Failed to set handler option '{key}': {opt_err}")

            # 5. 执行 handler（通过 payload 参数传递 payload_module）
            logger.info(f"Executing multi/handler with payload: {payload_name}")
            result = handler.execute(payload=payload_module)

            logger.info(f"Multi/handler executed successfully, result: {result}")
            return {
                "status": "success",
                "job_id": result.get('job_id') if result else None,
                "message": "Multi/handler executed successfully",
                "details": result
            }

        except Exception as e:
            logger.error(f"Failed to execute multi/handler: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Multi/handler execution failed: {str(e)}",
                "details": None
            }

    def _execute_regular_exploit(self, module_path, options=None, payload=None) -> Dict[str, Any]:
        """
        执行常规 exploit 模块（非 multi/handler）

        :param module_path: exploit模块路径
        :param options: 模块选项字典
        :param payload: payload名称
        :return: 执行结果字典
        """
        try:
            # 初始化
            if options is None:
                options = {}

            # 1. 选择 exploit 模块
            logger.info(f"Creating exploit module: {module_path}")
            exploit = self._client.modules.use('exploit', module_path)

            # 2. 如果指定了 payload，必须先设置 payload（这是 MSF 的要求）
            if payload:
                logger.info(f"Setting payload: {payload}")
                exploit['PAYLOAD'] = payload  # payload 作为模块属性单独设置

            # 3. 设置其他选项
            if options:
                logger.info(f"Setting exploit options: {options}")
                for key, value in options.items():
                    # 跳过 PAYLOAD 选项（防止前端错误地把它放在 options 里）
                    if key.upper() == 'PAYLOAD':
                        continue
                    exploit[key] = value

            # 4. 执行 exploit
            # 注意：execute() 可能会返回 job_id 或者直接创建 session
            logger.info(f"Executing exploit module: {module_path}")
            result = exploit.execute()

            # 5. 格式化返回结果
            return {
                "status": "success",
                "job_id": result.get('job_id') if result else None,
                "message": "Exploit executed successfully",
                "details": result
            }

        except Exception as e:
            logger.error(f"Failed to execute regular exploit {module_path}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Exploit execution failed: {str(e)}",
                "details": None
            }

    def get_modules(self, module_type: str = "exploit") -> List[str]:
        """Get list of available modules.

        Args:
            module_type: Type of module (exploit, auxiliary, payload, etc.)

        Returns:
            List of module names
        """
        try:
            if self._client is None:
                self.connect()

            if module_type == "exploit":
                return self._client.modules.exploits
            elif module_type == "auxiliary":
                return self._client.modules.auxiliary
            elif module_type == "payload":
                return self._client.modules.payloads
            elif module_type == "post":
                return self._client.modules.post
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to get modules: {e}")
            raise
