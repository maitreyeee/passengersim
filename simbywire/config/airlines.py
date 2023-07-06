from .named import Named


class Airline(Named, extra="forbid"):
    rm_system: str
