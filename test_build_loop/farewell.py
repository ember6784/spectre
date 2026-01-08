"""Farewell utilities for saying goodbye."""


def farewell(name: str) -> str:
    """Return a farewell message for the given name.

    Args:
        name: The name to say goodbye to. If empty, uses "friend".

    Returns:
        A farewell message string.
    """
    if not name:
        return "Goodbye, friend!"
    return f"Goodbye, {name}!"
