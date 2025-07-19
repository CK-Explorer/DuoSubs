"""
Subtitle utility functions for encoding, decoding, style serialization, and file 
extension handling.

This module provides helper functions for serializing and deserializing subtitle data, 
processing subtitle text, handling style conflicts, and determining subtitle file types
and formats.

Dependencies:
    - pysubs2: For subtitle and style handling.
    - pathlib: For file path and extension parsing.
"""

from pathlib import Path
from typing import Any, Dict, Tuple, Union

import pysubs2

from duosubs.common.constants import (
    SUPPORTED_NATIVE_SUB_EXT,
    SUPPORTED_TIME_BASED_SUB_EXT,
)
from duosubs.subtitle.field import SubtitleField


def _encode(obj: Any) -> Any:
    """
    Recursively encodes Python objects (including tuples) for JSON serialization.

    Args:
        obj (Any): The object to encode. Can be a tuple, list, dict, or primitive type.

    Returns:
        Any: Encoded object suitable for JSON serialization.
    """
    if isinstance(obj, tuple):
        return {"__tuple__": True, "items": [_encode(i) for i in obj]}
    elif isinstance(obj, list):
        return [_encode(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _encode(v) for k, v in obj.items()}
    else:
        return obj

def _decode(obj: Any) -> Any:
    """
    Recursively decodes objects previously encoded by _encode, restoring tuples and 
    nested structures.

    Args:
        obj (Any): The object to decode. Can be a dict, list, or primitive type.

    Returns:
        Any: Decoded Python object with original structure (tuples, lists, dicts).
    """
    if isinstance(obj, dict):
        if "__tuple__" in obj:
            return tuple(_decode(i) for i in obj["items"])
        else:
            return {k: _decode(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_decode(i) for i in obj]
    else:
        return obj

def _serialize_styles(styles: Dict[str, pysubs2.SSAStyle]) -> Dict[str, dict[str, Any]]:
    """
    Serializes SSAStyle objects to dictionaries, converting color fields to integers.

    Args:
        styles (Dict[str, pysubs2.SSAStyle]): Dictionary of style objects.

    Returns:
        dict:
        - name of the style (str)
        - Serialized style data.(dict[str, Any])
    """
    def color_to_int(color: pysubs2.Color) -> int:
        return (color.a << 24) | (color.b << 16) | (color.g << 8) | color.r

    def clean(style: pysubs2.SSAStyle) -> dict[str, Any]:
        d = style.__dict__.copy()
        for k, v in d.items():
            if isinstance(v, pysubs2.Color):
                d[k] = color_to_int(v)
        return d

    return {name: clean(style) for name, style in styles.items()}

def _deserialize_styles(
        style_dict: Dict[str, dict[str, Any]]
    ) -> Dict[str, pysubs2.SSAStyle]:
    """
    Deserializes style dictionaries back into SSAStyle objects, restoring color and 
    alignment fields.

    Args:
        style_dict (Dict[str, dict[str, Any]]): Dictionary of serialized style data.

    Returns:
        Dict[str, pysubs2.SSAStyle]: Dictionary of SSAStyle objects.
    """
    def int_to_color(value: int) -> pysubs2.Color:
        r = value & 0xFF
        g = (value >> 8) & 0xFF
        b = (value >> 16) & 0xFF
        a = (value >> 24) & 0xFF
        return pysubs2.Color(r=r, g=g, b=b, a=a)

    def restore(style_data: dict[str, Any]) -> pysubs2.SSAStyle:
        d = style_data.copy()
        for k, v in d.items():
            kl = k.lower()
            if isinstance(v, int) and kl.endswith("color"):
                d[k] = int_to_color(v)
            elif kl == "alignment":
                try:
                    d[k] = pysubs2.Alignment(v)
                except ValueError:
                    pass
        return pysubs2.SSAStyle(**d)

    return {name: restore(style_data) for name, style_data in style_dict.items()}

def _sub_processing(sub: SubtitleField, retain_newline: bool) -> Tuple[str, str]:
    """
    Processes subtitle text fields, optionally removing line breaks.

    Args:
        sub (SubtitleField): Subtitle field object containing primary and secondary 
            text.
        retain_newline (bool): Whether to retain line breaks ("\\N").

    Returns:
        tuple[str, str]:
        - Processed primary text.
        - Processed secondary text.
    """
    def text_processing(text: str, retain_newline: bool) -> str:
        if not retain_newline:
            text = text.replace("\\N", " ")
        return text

    primary_text: str = text_processing(sub.primary_text, retain_newline)
    secondary_text: str = text_processing(sub.secondary_text, retain_newline)

    return primary_text, secondary_text

def _get_format_name(value: Union[str, Path]) -> str:
    """
    Extracts the file extension or format name from a file path or string.

    Args:
        value (str | Path): File path or extension string.

    Returns:
        str: Lowercase extension or format name (without leading dot).
    """
    path = Path(value)
    suffix = path.suffix.lower()
    return suffix.lstrip(".") if suffix else str(value).lower().lstrip(".")

def _extension_type(save_path_or_extension: str) -> Tuple[bool, bool]:
    """
    Determines if a file extension is time-based or native, and checks for errors.

    Args:
        save_path_or_extension (str): File path or extension string.

    Returns:
        tuple[bool, bool]:
        - True if the file is time-based, False if native.
        - True if there is an error with the file type.
    """
    extension: str = _get_format_name(save_path_or_extension)
    time_based_subsfile: bool = False
    error: bool = False
    if extension in SUPPORTED_TIME_BASED_SUB_EXT:
        time_based_subsfile = True
    elif extension in SUPPORTED_NATIVE_SUB_EXT:
        time_based_subsfile = False
    else:
        error = True

    return time_based_subsfile, error

def _rename_common_styles(
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
    ) -> Tuple[pysubs2.SSAFile, Dict[str, str]]:
    """
    Renames common style names in secondary styles to avoid conflicts with primary 
    styles.

    Args:
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.

    Returns:
        tuple[pysubs2.SSAFile, Dict[str, str]]:
        - Updated secondary styles with renamed common styles.
        - Mapping of old style names to new names in secondary styles.
    """
    style_primary_name: set[str] = {name for name, _ in primary_styles.styles.items()}
    style_secondary_name: set[str] = {
        name for name, _ in secondary_styles.styles.items()
    }
    common_name: set[str] = style_primary_name & style_secondary_name

    replacement_dict: Dict[str, str] = {}
    for name in common_name:
        new_name: str = name + "_1"
        secondary_styles.rename_style(name, new_name)
        replacement_dict[name] = new_name

    return secondary_styles, replacement_dict
