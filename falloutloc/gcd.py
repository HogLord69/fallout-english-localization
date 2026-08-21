"""Premade character (`.GCD`) name field.

A GCD is 432 bytes. The display name is a fixed 32-byte, null-padded field
at offset 0x0174. Only that field is touched; the rest of the character --
stats, skills, traits, perks -- is left byte-for-byte alone.
"""
NAME_OFF = 0x0174
NAME_LEN = 32


def get_name(raw):
    return raw[NAME_OFF:NAME_OFF + NAME_LEN].split(b"\x00")[0].decode("cp1252", "replace")


def set_name(raw, name):
    encoded = name.encode("cp1252")
    if len(encoded) >= NAME_LEN:
        raise ValueError(f"name {name!r} does not fit in {NAME_LEN} bytes")
    field = encoded + b"\x00" * (NAME_LEN - len(encoded))
    return raw[:NAME_OFF] + field + raw[NAME_OFF + NAME_LEN:]
