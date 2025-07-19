"""
Subtitle writer module for saving and exporting subtitle data in various formats.

This module provides functions to save subtitle data and styles to files or memory, 
supporting compressed edit files, combined bilingual subtitles, and separate 
primary/secondary subtitle streams.

It handles style serialization, file format detection, and supports both time-based and 
native subtitle formats.

Dependencies:
    - pysubs2: For subtitle file and style handling.
    - gzip, io, json: For file I/O and serialization.
"""

import gzip
import io
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Union

import pysubs2

from duosubs.subtitle.field import SubtitleField

from .utils import (
    _encode,
    _extension_type,
    _get_format_name,
    _rename_common_styles,
    _serialize_styles,
    _sub_processing,
)


def save_file_edit(
        sub_list: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
        save_path: Union[Path, str]
    ) -> None:
    """
    Save subtitle data and styles to a compressed edit file (.json.gz).

    Args:
        sub_list (list[SubtitleField]): List of subtitle fields to save.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.
        save_path (Path | str): Path to save the compressed file (without .json.gz 
            extension).
    """
    data_to_save = _save_edit(
        sub_list,
        primary_styles,
        secondary_styles
    )
    save_path = Path(save_path)
    gz_path = save_path.with_suffix(save_path.suffix + ".gz")
    with gzip.open(gz_path, "wt", encoding="utf-8") as file:
        json.dump(
            _encode(data_to_save),
            file,
            separators=(",", ":")
        )

def save_memory_edit(
        sub_list: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
    ) -> bytes:
    """
    Save subtitle data and styles to a compressed edit file in memory.

    Args:
        sub_list (list[SubtitleField]): List of subtitle fields to save.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.

    Returns:
        bytes: Compressed file content as bytes.
    """
    data_to_save = _save_edit(
        sub_list,
        primary_styles,
        secondary_styles
    )

    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="w") as gz:
        json_bytes = json.dumps(
            _encode(data_to_save),
            separators=(",", ":")
        ).encode("utf-8")
        gz.write(json_bytes)

    return buffer.getvalue()

def save_file_combined(
        sub_list: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
        save_path: Union[Path, str],
        secondary_above: bool = True,
        retain_newline: bool = True
    ) -> None:
    """
    Save combined bilingual subtitles to a file, with both primary and secondary text in
    each event.

    Args:
        sub_list (list[SubtitleField]): List of subtitle fields to save.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.
        save_path (Path | str): Path to save the subtitle file.
        secondary_above (bool, optional): If True, secondary text is above primary. 
            Defaults to True.
        retain_newline (bool, optional): If True, retain line breaks. Defaults to True.
    """
    sub_pysubs2 = _save_combined(
        sub_list,
        primary_styles,
        secondary_styles,
        str(save_path),
        secondary_above,
        retain_newline,
    )

    _pysubs2_save(sub_pysubs2, str(save_path))

def save_memory_combined(
        sub_list: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
        extension_fmt: str,
        secondary_above: bool = True,
        retain_newline: bool = True
    ) -> bytes:
    """
    Save combined bilingual subtitles to memory as a string.

    Args:
        sub_list (list[SubtitleField]): List of subtitle fields to save.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.
        extension_fmt (str): Subtitle file format/extension.
        secondary_above (bool, optional): If True, secondary text is above primary. 
            Defaults to True.
        retain_newline (bool, optional): If True, retain line breaks. Defaults to True.

    Returns:
        bytes: Subtitle file content as a UTF-8 encoded bytes.
    """
    sub_pysubs2 = _save_combined(
        sub_list,
        primary_styles,
        secondary_styles,
        extension_fmt,
        secondary_above,
        retain_newline,
    )

    return sub_pysubs2.to_string(extension_fmt).encode("utf-8")

def save_file_separate(
        sub_list: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
        save_path_primary: Union[Path, str],
        save_path_secondary: Union[Path, str],
        retain_newline: bool = True
    ) -> None:
    """
    Save primary and secondary subtitles as separate files.

    Args:
        sub_list (list[SubtitleField]): List of subtitle fields to save.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.
        save_path_primary (Path | str): Path to save the primary subtitle file.
        save_path_secondary (Path | str): Path to save the secondary subtitle file.
        retain_newline (bool, optional): If True, retain line breaks. Defaults to True.
    """
    sub_pysubs2_primary, sub_pysubs2_secondary = _save_separate(
        sub_list,
        primary_styles,
        secondary_styles,
        str(save_path_primary),
        str(save_path_secondary),
        retain_newline
    )

    _pysubs2_save(sub_pysubs2_primary, str(save_path_primary))
    _pysubs2_save(sub_pysubs2_secondary, str(save_path_secondary))

def save_memory_separate(
        sub_list: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
        extension_primary: str,
        extension_secondary: str,
        retain_newline: bool = True
    ) -> tuple[bytes,bytes]:
    """
    Save primary and secondary subtitles as separate files in memory.

    Args:
        sub_list (list[SubtitleField]): List of subtitle fields to save.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.
        extension_primary (str): File format/extension for primary subtitles.
        extension_secondary (str): File format/extension for secondary subtitles.
        retain_newline (bool, optional): If True, retain line breaks. Defaults to True.

    Returns:
        tuple[bytes, bytes]:
        - UTF-8 encoded bytes for primary subtitles.
        - UTF-8 encoded bytes for secondary subtitles.
    """
    sub_pysubs2_primary, sub_pysubs2_secondary = _save_separate(
        sub_list,
        primary_styles,
        secondary_styles,
        extension_primary,
        extension_secondary,
        retain_newline
    )

    primary_bytes = sub_pysubs2_primary.to_string(extension_primary).encode("utf-8")
    secondary_bytes = sub_pysubs2_secondary.to_string(
        extension_secondary
    ).encode("utf-8")

    return primary_bytes, secondary_bytes

def _pysubs2_save(sub: pysubs2.SSAFile, file_path: str) -> None:
    """
    Save a pysubs2.SSAFile object to disk using the correct format.

    Args:
        sub (pysubs2.SSAFile): Subtitle file object to save.
        file_path (str): Path to save the file.
    """
    ext = _get_format_name(file_path)
    sub.save(file_path, format_=ext)

def _save_edit(
        sub_list: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
    ) -> dict[str,Any]:
    """
    Prepare subtitle data and styles for saving as an edit file.

    Args:
        sub_list (list[SubtitleField]): List of subtitle fields.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.

    Returns:
        dict[str, Any]: Dictionary containing styles and subtitle data.
    """
    data_to_save = {
        "primary_styles": _serialize_styles(primary_styles.styles),
        "secondary_styles": _serialize_styles(secondary_styles.styles),
        "subtitles": [asdict(sub) for sub in sub_list]
    }

    return data_to_save

def _save_combined(
        sub_list: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
        save_path_or_extension: str,
        secondary_above: bool,
        retain_newline: bool,
    ) -> pysubs2.SSAFile:
    """
    Prepare a combined bilingual subtitle file for saving.

    Args:
        sub_list (list[SubtitleField]): List of subtitle fields.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.
        save_path_or_extension (str): File path or extension for output.
        secondary_above (bool): If True, secondary text is above primary.
        retain_newline (bool): If True, retain line breaks.

    Returns:
        pysubs2.SSAFile: Combined subtitle file object.
    
    Raises:
        ValueError: If the file type for saving subtitles is invalid.
    """
    time_based_subsfile, error_file = _extension_type(save_path_or_extension)
    if error_file:
        raise ValueError("Invalid file type for saving subtitles.")

    sub_pysubs2 = pysubs2.SSAFile()
    secondary_styles_copy = pysubs2.SSAFile()
    secondary_styles_copy.import_styles(secondary_styles)
    secondary_styles_copy, replacement_dict = _rename_common_styles(
        primary_styles,
        secondary_styles_copy
    )
    sub_pysubs2.import_styles(primary_styles)
    sub_pysubs2.import_styles(secondary_styles_copy)

    for sub in sub_list:
        primary_text, secondary_text = _sub_processing(
            sub,
            retain_newline
        )

        text1 = secondary_text if secondary_above else primary_text
        text2 = primary_text if secondary_above else secondary_text

        style1 = (
            replacement_dict.get(sub.secondary_style, sub.secondary_style)
            if secondary_above
            else sub.primary_style
        )
        style2 = (
            sub.primary_style
            if secondary_above
            else replacement_dict.get(sub.secondary_style, sub.secondary_style)
        )

        combined_text = (
            f"{text1}\\N{text2}"
            if time_based_subsfile
            else f"{text1}\\N{{\\r{style2}}}{text2}"
        )
        event = pysubs2.SSAEvent(
            start=sub.start,
            end=sub.end,
            text=combined_text,
            style=style1
        )
        sub_pysubs2.events.append(event)

    return sub_pysubs2

def _save_separate(
        sub_list: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
        save_path_primary_or_extension: str,
        save_path_secondary_or_extension: str,
        retain_newline: bool = True
    ) -> tuple[pysubs2.SSAFile,pysubs2.SSAFile]:
    """
    Prepare separate primary and secondary subtitle files for saving.

    Args:
        sub_list (list[SubtitleField]): List of subtitle fields.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.
        save_path_primary_or_extension (str): File path or extension for primary 
            subtitles.
        save_path_secondary_or_extension (str): File path or extension for secondary 
            subtitles.
        retain_newline (bool, optional): If True, retain line breaks. Defaults to True.

    Returns:
        tuple[pysubs2.SSAFile,pysubs2.SSAFile]:
        - Primary subtitle file object.
        - Secondary subtitle file object.
    
    Raises:
        ValueError: If the file type for saving subtitles is invalid.
    """
    _, error_primary = _extension_type(save_path_primary_or_extension)
    _, error_secondary = _extension_type(save_path_secondary_or_extension)
    if error_primary or error_secondary:
        raise ValueError("Invalid file type for saving subtitles.")

    sub_pysubs2_primary = pysubs2.SSAFile()
    sub_pysubs2_secondary = pysubs2.SSAFile()

    sub_pysubs2_primary.import_styles(primary_styles)
    sub_pysubs2_secondary.import_styles(secondary_styles)

    for sub in sub_list:
        primary_text, secondary_text = _sub_processing(
            sub,
            retain_newline
        )

        event = pysubs2.SSAEvent(
            start=sub.start,
            end=sub.end,
            text=primary_text,
            style=sub.primary_style
        )
        sub_pysubs2_primary.events.append(event)

        event = pysubs2.SSAEvent(
            start=sub.start,
            end=sub.end,
            text=secondary_text,
            style=sub.secondary_style
        )
        sub_pysubs2_secondary.events.append(event)

    return sub_pysubs2_primary, sub_pysubs2_secondary
