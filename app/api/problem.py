"""Problem / counseling submission endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.problem import Problem
from app.models.user import RoleEnum, User
from app.schemas.problem import AdminResponseUpdate, ProblemCreate, ProblemOut

router = APIRouter(prefix="/problem", tags=["Problem Counseling"])


@router.post("/submit", response_model=ProblemOut)
def submit_problem(
    data: ProblemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Problem:
    problem = Problem(**data.model_dump(), submitter_id=current_user.id)
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


@router.get("/list", response_model=List[ProblemOut])
def get_problems(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.admin:
        return db.query(Problem).all()
    return db.query(Problem).filter(Problem.submitter_id == current_user.id).all()


@router.get("/{problem_id}", response_model=ProblemOut)
def get_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Problem:
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    if current_user.role != RoleEnum.admin and problem.submitter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return problem


@router.patch("/{problem_id}/respond")
def respond_to_problem(
    problem_id: int,
    data: AdminResponseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    problem.admin_response = data.admin_response
    problem.status = data.status
    db.commit()
    return {"message": "Response submitted"}
