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

    def stop_session(self, session_id: int) -> Dict[str, Any]:
        """
        Stop a specific MSF session.

        Args:
            session_id: The ID of the session to stop

        Returns:
            Dictionary with status and message
        """
        try:
            # 确保连接
            if self._client is None:
                self.connect()

            # 将 session_id 转换为字符串（MSF RPC 使用字符串类型的会话 ID）
            str_id = str(session_id)

            # 获取当前会话列表（字典，键为字符串类型的 ID）
            sessions = self._client.sessions.list
            logger.info(f"Current sessions: {list(sessions.keys())}")

            # 检查会话是否存在
            if str_id not in sessions:
                logger.warning(f"Session ID {session_id} (string: {str_id}) does not exist")
                return {
                    "status": "error",
                    "message": f"Session ID {session_id} does not exist"
                }

            # 停止指定会话
            logger.info(f"Attempting to stop session {session_id} (string: {str_id})")
            self._client.sessions.session(str_id).stop()

            logger.info(f"Session {session_id} (string: {str_id}) stopped successfully")
            return {
                "status": "success",
                "message": f"Session {session_id} stopped"
            }
        except Exception as e:
            logger.error(f"Error stopping session {session_id}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

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
        :return: 执行结果字典，包含session_id
        """
        # 记录执行日志
        logger.info(f"Executing exploit: module={module_path}, payload={payload}, options={options}")

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
                "success": False,
                "message": f"Exploit execution failed: {str(e)}",
                "session_id": None,
                "output": None
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
        :return: 执行结果字典，包含session_id
        """
        try:
            # 初始化 options 为空字典
            if options is None:
                options = {}

            # 获取 payload 名称（优先从 payload 参数，其次从 options['PAYLOAD']）
            payload_name = payload or options.get('PAYLOAD') or options.get('payload')

            if not payload_name:
                return {
                    "success": False,
                    "message": "Payload is required for multi/handler module",
                    "session_id": None,
                    "output": None
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

            # 6. 获取新创建的会话ID
            session_id = self._get_new_session_id()

            logger.info(f"Multi/handler executed successfully, result: {result}, session_id: {session_id}")
            return {
                "success": True,
                "message": "Multi/handler executed successfully",
                "session_id": session_id,
                "job_id": result.get('job_id') if result else None,
                "output": result
            }

        except Exception as e:
            logger.error(f"Failed to execute multi/handler: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Multi/handler execution failed: {str(e)}",
                "session_id": None,
                "output": None
            }

    def _get_new_session_id(self) -> Optional[str]:
        """Get the most recently created session ID.

        Returns:
            Session ID as string, or None if no sessions exist
        """
        try:
            sessions = self._client.sessions.list
            if sessions:
                # Return the most recent session ID (last in dict)
                return list(sessions.keys())[-1]
            return None
        except Exception as e:
            logger.warning(f"Failed to get session ID: {e}")
            return None

    def _execute_regular_exploit(self, module_path, options=None, payload=None) -> Dict[str, Any]:
        """
        执行常规 exploit 模块（非 multi/handler）

        :param module_path: exploit模块路径
        :param options: 模块选项字典
        :param payload: payload名称
        :return: 执行结果字典，包含session_id
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

            # 5. 获取新创建的会话ID
            session_id = self._get_new_session_id()

            # 6. 格式化返回结果
            return {
                "success": True,
                "message": "Exploit executed successfully",
                "session_id": session_id,
                "job_id": result.get('job_id') if result else None,
                "output": result
            }

        except Exception as e:
            logger.error(f"Failed to execute regular exploit {module_path}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Exploit execution failed: {str(e)}",
                "session_id": None,
                "output": None
            }

    def get_modules(self, module_type: str = "exploit", keyword: str = None) -> List[Dict[str, Any]]:
        """Get list of available modules with optional filtering and search.

        Args:
            module_type: Type of module (exploit, auxiliary, payload, encoder, nop, post)
            keyword: Optional keyword for fuzzy matching module names

        Returns:
            List of module information dictionaries
        """
        try:
            if self._client is None:
                self.connect()

            # Get module list based on type
            if module_type == "exploit":
                module_list = self._client.modules.exploits
            elif module_type == "auxiliary":
                module_list = self._client.modules.auxiliary
            elif module_type == "payload":
                module_list = self._client.modules.payloads
            elif module_type == "post":
                module_list = self._client.modules.post
            elif module_type == "encoder":
                module_list = self._client.modules.encoders
            elif module_type == "nop":
                module_list = self._client.modules.nops
            else:
                return []

            # Apply keyword filtering if provided
            if keyword:
                keyword_lower = keyword.lower()
                module_list = [m for m in module_list if keyword_lower in m.lower()]

            # Get module details
            modules = []
            for module_name in module_list[:1000]:  # Limit to prevent timeout
                try:
                    module = self._client.modules.use(module_type, module_name)
                    modules.append({
                        "name": module_name,
                        "fullname": module_name,
                        "description": getattr(module, "description", ""),
                        "rank": getattr(module, "rank", 0),
                        "type": module_type
                    })
                except Exception as e:
                    logger.debug(f"Failed to load module {module_name}: {e}")
                    continue

            return modules
        except Exception as e:
            logger.error(f"Failed to get modules: {e}")
            raise

    def get_module_options(self, module_name: str, payload: str = None) -> List[Dict[str, Any]]:
        """Get options/parameters for a specific module, optionally merged with payload options.

        Args:
            module_name: Full module path (e.g., 'exploit/windows/smb/ms17_010_eternalblue')
            payload: Optional payload name (e.g., 'windows/x64/meterpreter/reverse_tcp')

        Returns:
            List of option dictionaries
        """
        try:
            if self._client is None:
                self.connect()

            # Determine module type from path
            parts = module_name.split('/')
            if len(parts) < 2:
                raise ValueError(f"Invalid module name: {module_name}")

            module_type = parts[0]

            # Create module instance
            module = self._client.modules.use(module_type, module_name)

            # Get module options
            options_dict = self._parse_module_options(module.options)

            # If payload is provided, get payload options and merge
            if payload:
                try:
                    payload_module = self._client.modules.use('payload', payload)
                    payload_options = self._parse_module_options(payload_module.options)
                    # Merge: module options first, then payload options (payload can override)
                    options_dict.update(payload_options)
                    logger.info(f"Merged module options with payload {payload}")
                except Exception as e:
                    logger.warning(f"Failed to get payload options for {payload}: {e}")

            # Convert to list
            options = list(options_dict.values())

            logger.info(f"Retrieved {len(options)} options for module {module_name}" + (f" with payload {payload}" if payload else ""))
            return options

        except Exception as e:
            logger.error(f"Failed to get options for module {module_name}: {e}")
            raise

    def _parse_module_options(self, module_options) -> Dict[str, Dict[str, Any]]:
        """Parse module options into a dictionary.

        Args:
            module_options: Raw options from MSF module

        Returns:
            Dictionary of option_name -> option_details
        """
        options_dict = {}

        if not module_options:
            return options_dict

        # Handle case where options is a list
        if isinstance(module_options, list):
            for opt in module_options:
                if isinstance(opt, dict):
                    options_dict[opt.get('name', '')] = {
                        "name": opt.get('name', ''),
                        "required": opt.get('required', False),
                        "default": opt.get('default'),
                        "description": opt.get('description', ''),
                        "type": opt.get('type', 'string')
                    }
                elif isinstance(opt, str):
                    options_dict[opt] = {
                        "name": opt,
                        "required": False,
                        "default": None,
                        "description": "",
                        "type": "string"
                    }
        # Handle case where options is a dictionary
        elif isinstance(module_options, dict):
            for opt_name, opt_info in module_options.items():
                # Parse option info
                if isinstance(opt_info, dict):
                    options_dict[opt_name] = {
                        "name": opt_name,
                        "required": opt_info.get('required', False),
                        "default": opt_info.get('default'),
                        "description": opt_info.get('description', ''),
                        "type": opt_info.get('type', 'string')
                    }
                else:
                    # Fallback for simpler format
                    options_dict[opt_name] = {
                        "name": opt_name,
                        "required": False,
                        "default": str(opt_info) if opt_info else None,
                        "description": "",
                        "type": "string"
                    }

        return options_dict

    def get_compatible_payloads(self, module_name: str) -> List[str]:
        """Get compatible payloads for an exploit module.

        Args:
            module_name: Full module path (e.g., 'exploit/windows/smb/ms17_010_eternalblue')

        Returns:
            List of compatible payload names
        """
        try:
            if self._client is None:
                self.connect()

            # Determine module type from path
            parts = module_name.split('/')
            if len(parts) < 2:
                raise ValueError(f"Invalid module name: {module_name}")

            module_type = parts[0]

            # Only exploit modules have compatible payloads
            if module_type != 'exploit':
                logger.warning(f"Module {module_name} is not an exploit module, returning empty list")
                return []

            # Create module instance
            module = self._client.modules.use(module_type, module_name)

            # Get compatible payloads - try multiple approaches
            payloads = []

            # Try method 1: as attribute (list)
            if hasattr(module, 'compatible_payloads'):
                try:
                    # Try calling as method first
                    try:
                        compatible = module.compatible_payloads()
                    except TypeError:
                        # If not callable, try as property
                        compatible = module.compatible_payloads

                    if compatible:
                        # Handle different return types
                        if isinstance(compatible, list):
                            for p in compatible:
                                if isinstance(p, dict):
                                    name = p.get('name', p.get('refname', ''))
                                    if name:
                                        payloads.append(name)
                                elif isinstance(p, str):
                                    payloads.append(p)
                        elif isinstance(compatible, dict):
                            for key in compatible.keys():
                                payloads.append(key)
                        elif hasattr(compatible, '__iter__'):
                            # Handle generators or other iterables
                            for p in compatible:
                                if isinstance(p, dict):
                                    payloads.append(p.get('name', ''))
                                elif isinstance(p, str):
                                    payloads.append(p)
                except Exception as e:
                    logger.debug(f"Failed to get compatible_payloads: {e}")

            # If still empty, try direct RPC call
            if not payloads:
                try:
                    result = self._client.call('module.compatible_payloads', [module_name])
                    if isinstance(result, dict):
                        payloads = result.get('payloads', [])
                    elif isinstance(result, list):
                        payloads = result
                except Exception as e:
                    logger.debug(f"RPC call failed: {e}")

            # Filter out empty strings
            payloads = [p for p in payloads if p]

            logger.info(f"Retrieved {len(payloads)} compatible payloads for module {module_name}")
            return payloads

        except Exception as e:
            logger.error(f"Failed to get compatible payloads for module {module_name}: {e}")
            raise

    def get_modules_detail(self, module_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get detailed list of available modules with metadata.

        Args:
            module_type: Type of module (exploit, auxiliary, payload, encoder, nop, post).
                        If None, returns all module types.

        Returns:
            List of module information dictionaries
        """
        try:
            if self._client is None:
                self.connect()

            modules = []
            module_types = [module_type] if module_type else ["exploit", "auxiliary", "payload", "encoder", "nop", "post"]

            for mtype in module_types:
                try:
                    if mtype == "exploit":
                        module_list = self._client.modules.exploits
                    elif mtype == "auxiliary":
                        module_list = self._client.modules.auxiliary
                    elif mtype == "payload":
                        module_list = self._client.modules.payloads
                    elif mtype == "post":
                        module_list = self._client.modules.post
                    elif mtype == "encoder":
                        module_list = self._client.modules.encoders
                    elif mtype == "nop":
                        module_list = self._client.modules.nops
                    else:
                        continue

                    # Get details for each module
                    for module_name in module_list:
                        try:
                            module = self._client.modules.use(mtype, module_name)
                            modules.append({
                                "name": module_name,
                                "fullname": module_name,
                                "description": getattr(module, "description", ""),
                                "rank": getattr(module, "rank", 0),
                                "type": mtype
                            })
                        except Exception as e:
                            # Skip modules that can't be loaded
                            logger.debug(f"Failed to load module {module_name}: {e}")
                            continue

                except Exception as e:
                    logger.warning(f"Failed to get modules of type {mtype}: {e}")
                    continue

            logger.info(f"Retrieved {len(modules)} modules")
            return modules

        except Exception as e:
            logger.error(f"Failed to get modules detail: {e}")
            raise
