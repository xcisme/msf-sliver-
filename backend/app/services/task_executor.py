"""Task executor service for running attack tasks in background."""
import logging
from datetime import datetime
from typing import Optional

from app.core.database import SessionLocal
from app.models.task import AttackTask
from app.models.user import User
from app.utils.msf_client import MsfClient
from app.core.config import settings
from app.services.log_service import add_log

logger = logging.getLogger(__name__)


async def execute_attack_task(task_id: int) -> None:
    """Execute an attack task in the background.

    Args:
        task_id: The ID of the task to execute
    """
    db = SessionLocal()
    try:
        task = db.query(AttackTask).filter(AttackTask.id == task_id).first()
        if not task:
            logger.warning(f"Task {task_id} not found")
            return

        # Update status to running
        task.status = "running"
        db.commit()

        logger.info(f"Starting execution of task {task_id}: {task.module_name}")

        # Execute the exploit using MSF client
        try:
            msf_client = MsfClient(
                host=settings.MSF_HOST,
                port=settings.MSF_PORT,
                password=settings.MSF_PASSWORD,
                username=settings.MSF_USERNAME
            )

            result = msf_client.execute_exploit(
                module_path=task.module_name,
                options=task.options or {},
                payload=task.payload
            )

            # Check result and update task
            if result.get("success"):
                task.status = "success"
                task.session_id = result.get("session_id")
                task.output = str(result.get("output", ""))
                logger.info(f"Task {task_id} completed successfully, session: {task.session_id}")

                # Log successful execution
                add_log(
                    db=db,
                    user_id=task.user_id,
                    action="EXECUTE_TASK",
                    result="SUCCESS",
                    target=task.module_name,
                    detail=f"Exploit执行成功，会话ID: {task.session_id}",
                    ip_address=None
                )
            else:
                task.status = "failed"
                task.output = result.get("message", "Unknown error")
                logger.error(f"Task {task_id} failed: {task.output}")

                # Log failed execution
                add_log(
                    db=db,
                    user_id=task.user_id,
                    action="EXECUTE_TASK",
                    result="FAILED",
                    target=task.module_name,
                    detail=f"Exploit执行失败: {task.output}",
                    ip_address=None
                )

        except Exception as e:
            task.status = "failed"
            task.output = str(e)
            logger.error(f"Task {task_id} execution error: {e}")

            # Log execution error
            add_log(
                db=db,
                user_id=task.user_id,
                action="EXECUTE_TASK",
                result="FAILED",
                target=task.module_name,
                detail=f"Exploit执行异常: {str(e)}",
                ip_address=None
            )

        # Set finished timestamp
        task.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Error executing task {task_id}: {e}")
        try:
            task = db.query(AttackTask).filter(AttackTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.output = str(e)
                task.finished_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def stop_task(task_id: int) -> Optional[dict]:
    """Stop a running task by terminating its session.

    Args:
        task_id: The ID of the task to stop

    Returns:
        Result dictionary
    """
    db = SessionLocal()
    try:
        task = db.query(AttackTask).filter(AttackTask.id == task_id).first()
        if not task:
            return {"success": False, "message": "Task not found"}

        # If task has an active session, try to stop it
        if task.session_id:
            try:
                msf_client = MsfClient(
                    host=settings.MSF_HOST,
                    port=settings.MSF_PORT,
                    password=settings.MSF_PASSWORD,
                    username=settings.MSF_USERNAME
                )
                result = msf_client.stop_session(int(task.session_id))
                logger.info(f"Stopped session {task.session_id} for task {task_id}: {result}")

                # Log session termination
                add_log(
                    db=db,
                    user_id=task.user_id,
                    action="STOP_TASK",
                    result="SUCCESS",
                    target=task.module_name,
                    detail=f"终止会话 {task.session_id}，任务ID: {task_id}",
                    ip_address=None
                )
            except Exception as e:
                logger.warning(f"Failed to stop session {task.session_id}: {e}")

        # Update task status
        task.status = "failed"
        task.output = "Task stopped by user"
        task.finished_at = datetime.utcnow()
        db.commit()

        return {"success": True, "message": "Task stopped"}

    except Exception as e:
        logger.error(f"Error stopping task {task_id}: {e}")
        return {"success": False, "message": str(e)}
    finally:
        db.close()