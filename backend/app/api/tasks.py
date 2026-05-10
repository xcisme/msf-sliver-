"""Attack tasks API endpoints."""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user as get_user
from app.core.database import get_db
from app.models.task import AttackTask
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskListResponse
from app.services.task_executor import execute_attack_task, stop_task
from app.services.log_service import add_log

router = APIRouter(prefix="/api/msf/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> TaskResponse:
    """Create a new attack task.

    Requires JWT authentication.

    Args:
        task_in: Task creation data
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        db: Database session

    Returns:
        Created task
    """
    # Create task record
    task = AttackTask(
        user_id=current_user.id,
        module_name=task_in.module_name,
        payload=task_in.payload,
        options=task_in.options,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Record task creation
    add_log(
        db=db,
        user_id=current_user.id,
        action="CREATE_TASK",
        result="SUCCESS",
        target=task_in.module_name,
        detail=f"创建攻击任务: {task_in.module_name}",
        ip_address=None
    )

    # Start background execution
    background_tasks.add_task(execute_attack_task, task.id)

    logger.info(f"Task {task.id} created by user {current_user.id}")
    return task


@router.get("", response_model=TaskListResponse)
async def get_tasks(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> TaskListResponse:
    """Get attack tasks for current user.

    Requires JWT authentication.

    Args:
        status_filter: Optional status filter
        page: Page number
        limit: Items per page
        current_user: Authenticated user
        db: Database session

    Returns:
        List of tasks with pagination info
    """
    query = db.query(AttackTask).filter(AttackTask.user_id == current_user.id)

    if status_filter:
        query = query.filter(AttackTask.status == status_filter)

    # Get total count
    total = query.count()

    # Get paginated results
    offset = (page - 1) * limit
    tasks = query.order_by(AttackTask.created_at.desc()).offset(offset).limit(limit).all()

    return TaskListResponse(total=total, items=tasks)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
) -> TaskResponse:
    """Get a specific task by ID.

    Requires JWT authentication.

    Args:
        task_id: Task ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Task details

    Raises:
        HTTPException: If task not found or not owned by user
    """
    task = db.query(AttackTask).filter(
        AttackTask.id == task_id,
        AttackTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
):
    """Delete a task.

    Requires JWT authentication.

    Args:
        task_id: Task ID
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: If task not found or not owned by user
    """
    task = db.query(AttackTask).filter(
        AttackTask.id == task_id,
        AttackTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # If task is running, try to stop it first
    if task.status == "running" and task.session_id:
        stop_task(task_id)

    db.delete(task)
    db.commit()

    logger.info(f"Task {task_id} deleted by user {current_user.id}")


@router.post("/{task_id}/stop")
async def stop_task_endpoint(
    task_id: int,
    current_user: User = Depends(get_user),
    db: Session = Depends(get_db)
):
    """Stop a running task.

    Requires JWT authentication.

    Args:
        task_id: Task ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Result of stopping the task
    """
    task = db.query(AttackTask).filter(
        AttackTask.id == task_id,
        AttackTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot stop task with status: {task.status}"
        )

    result = stop_task(task_id)
    if result.get("success"):
        return {"status": "success", "message": result.get("message")}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message")
        )