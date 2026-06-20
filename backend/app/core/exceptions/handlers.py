from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions.document import FileTooLargeError, UnsupportedFileTypeError

from app.core.exceptions.auth import (
    AuthenticationError,
    EmailAlreadyExistsError,
    UserNotFoundError,
)

from app.core.exceptions.conversation import (
    ConversationAccessDeniedError,
    ConversationDeleteDeniedError,
    ConversationNotFoundError,
    ConversationRenameDeniedError,
)

def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(EmailAlreadyExistsError)
    async def email_already_exists_handler(
        request: Request,
        exc: EmailAlreadyExistsError,
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": "AUTH_001",
            },
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request,
        exc: AuthenticationError,
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": "AUTH_002",
            },
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(
        request: Request,
        exc: UserNotFoundError,
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": "AUTH_003",
            },
        )
    
    @app.exception_handler(UnsupportedFileTypeError)
    async def unsupported_file_type_handler(
        request: Request,
        exc: UnsupportedFileTypeError,
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": "DOC_001",
            },
        )

    @app.exception_handler(FileTooLargeError)
    async def file_too_large_handler(
        request: Request,
        exc: FileTooLargeError,
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": "DOC_002",
            },
        )
    


    @app.exception_handler(ConversationNotFoundError)
    async def conversation_not_found_handler(
        request: Request,
        exc: ConversationNotFoundError,
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": "CONV_001",
            },
        )


    @app.exception_handler(ConversationAccessDeniedError)
    async def conversation_access_denied_handler(
        request: Request,
        exc: ConversationAccessDeniedError,
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": "CONV_002",
            },
        )


    @app.exception_handler(ConversationRenameDeniedError)
    async def conversation_rename_denied_handler(
        request: Request,
        exc: ConversationRenameDeniedError,
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": "CONV_003",
            },
        )


    @app.exception_handler(ConversationDeleteDeniedError)
    async def conversation_delete_denied_handler(
        request: Request,
        exc: ConversationDeleteDeniedError,
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "error_code": "CONV_004",
            },
        )