"""
Custom exception classes for error handling in the subtitle merging pipeline.

These exceptions are used throughout the merge_pipeline and CLI to provide clear error 
reporting for different stages of the subtitle merging process.
"""
from typing import Optional


class LoadSubsError(Exception):
    """
    Exception raised when loading subtitle files fails.

    Args:
        message (str): Description of the error.
        original_exception (Exception, optional): The original exception that caused 
            the error.
    """
    def __init__(
            self,
            message: str,
            original_exception: Optional[Exception] = None
        ) -> None:
        super().__init__(f"{message} {original_exception}")
        self.original_exception: Exception | None = original_exception

class LoadModelError(Exception):
    """
    Exception raised when loading the sentence transformer model fails.

    Args:
        message (str): Description of the error.
        original_exception (Exception, optional): The original exception that caused 
            the error.
    """
    def __init__(
            self,
            message: str,
            original_exception: Optional[Exception] = None
        ) -> None:
        super().__init__(f"{message} {original_exception}")
        self.original_exception: Exception | None = original_exception

class MergeSubsError(Exception):
    """
    Exception raised when merging subtitles fails.

    Args:
        message (str): Description of the error.
        original_exception (Exception, optional): The original exception that caused 
            the error.
    """
    def __init__(
            self, 
            message: str,
            original_exception: Optional[Exception] = None
        ) -> None:
        super().__init__(f"{message} {original_exception}")
        self.original_exception: Exception | None = original_exception

class SaveSubsError(Exception):
    """
    Exception raised when saving subtitle files fails.

    Args:
        message (str): Description of the error.
        original_exception (Exception, optional): The original exception that caused 
            the error.
    """
    def __init__(
            self,
            message: str,
            original_exception: Optional[Exception] = None
        ) -> None:
        super().__init__(f"{message} {original_exception}")
        self.original_exception: Exception | None = original_exception
