import logging

def safe_error_message(e: Exception, fallback: str = "An internal server error occurred") -> str:
    """
    Logs the real error internally to avoid leaking sensitive information (like paths or DB internals)
    to the client, and returns a safe fallback message.
    """
    logging.error(f"Internal error: {str(e)}", exc_info=True)
    return fallback
