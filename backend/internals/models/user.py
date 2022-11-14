from dataclasses import dataclass

__all__ = (
    "PartialLogin",
    "PartialRegister",
)


@dataclass
class PartialLogin:
    """A partial login object that is used to store the login information
    before the user is logged in.
    """

    email: str
    password: str
    remember: bool = False


@dataclass
class PartialRegister:
    """A partial register object that is used to store the register information
    before the user is registered.
    """

    email: str
    password: str
    name: str
