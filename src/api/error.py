from abc import ABC, abstractmethod
from typing import Optional
from fastapi import status


from libs.result import Error


class APIError(Exception, ABC):
    @abstractmethod
    def get_status_code(self) -> int:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def get_reason(self):
        pass

    @abstractmethod
    def get_headers(self):
        pass

    def __init__(
        self, base_error: Error, status_code: int, headers: Optional[dict] = None
    ):
        self.base_error = base_error
        self.status_code = status_code
        self.headers = headers
        super().__init__(base_error.message)


class ClientError(APIError):
    """
    Error class for client errors (4xx).
    """

    def __init__(
        self,
        base_error: Error,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: Optional[dict] = None,
    ):
        super().__init__(base_error, status_code, headers)

    def to_dict(self):
        return {"code": self.base_error.code, "message": self.base_error.message}

    def get_status_code(self) -> int:
        return self.status_code

    def get_reason(self):
        return self.base_error.reason

    def get_headers(self):
        return self.headers


class ServerError(APIError):
    """
    Error class for server errors (5xx).
    """

    def __init__(
        self,
        base_error: Error,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: Optional[dict] = None,
    ):
        super().__init__(base_error, status_code, headers)

    def to_dict(self):
        return {"code": self.base_error.code, "message": "Internal server error"}

    def get_reason(self):
        return self.base_error.reason

    def get_status_code(self) -> int:
        return self.status_code

    def get_headers(self):
        return self.headers
