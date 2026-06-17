from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "AI Customer Support Platform API is running"
    }


@router.get("/health")
def health_check():
    return {
        "status": "healthy"
    }