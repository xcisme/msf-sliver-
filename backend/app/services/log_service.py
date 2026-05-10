"""统一日志记录服务"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.log import OperationLog


def add_log(
    db: Session,
    user_id: int,
    action: str,
    result: str = "SUCCESS",
    target: Optional[str] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None
) -> OperationLog:
    """添加操作日志

    Args:
        db: 数据库会话
        user_id: 用户ID
        action: 操作类型 (LOGIN, LOGOUT, CREATE_TASK, EXECUTE_TASK, etc.)
        result: 操作结果 (SUCCESS, FAILED, etc.)
        target: 操作目标 (模块名、会话ID等)
        detail: 详细信息
        ip_address: 客户端IP地址
    """
    log = OperationLog(
        user_id=user_id,
        action=action,
        target=target,
        result=result,
        detail=detail,
        ip_address=ip_address,
        created_at=datetime.now()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log