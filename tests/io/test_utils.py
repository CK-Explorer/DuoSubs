"""
Unit tests for subtitle utility functions in duosubs.io.utils.

This module contains pytest-based unit tests for encoding/decoding, style serialization,
sub processing, file format detection, and style name conflict resolution utilities.
"""
from pathlib import Path
from typing import TypedDict, cast

import pysubs2
import pytest

from duosubs.io.utils import (
    _decode,
    _deserialize_styles,
    _encode,
    _extension_type,
    _get_format_name,
    _rename_common_styles,
    _serialize_styles,
    _sub_processing,
)
from duosubs.subtitle.field import SubtitleField
from tests.common_utils.utils import load_test_cases

# Test cases paths
DATA_PATH: Path = Path(__file__).parent / "data"
DATA_SUB_PROCESSING: Path = DATA_PATH / "sub_processing.yaml"
DATA_GET_FORMAT_NAME: Path = DATA_PATH / "get_format_name.yaml"
DATA_EXT_TYPE: Path = DATA_PATH / "extension_type.yaml"

# ----------------------------
# TypedDict Definitions for Tests
# ----------------------------

class SubProcessingTest(TypedDict):
    """
    Represents a test case for sub processing function.

    Attributes:
        text (str): Input text to be processed.
        expected (str): Expected output after processing.
    """
    text: str
    expected: str

class GetFormatNameTest(TypedDict):
    """
    Represents a test case for getting file format name.

    Attributes:
        input (str): Input file path.
        expected (str): Expected format name.
    """
    input: str
    expected: str

class ExtensionTypeTest(TypedDict):
    """
    Represents a test case for file extension type detection.

    Attributes:
        input (str): Input file path.
        time_based (bool): Whether the file is time-based.
        error (bool): Whether an error occurred during detection.
    """
    input: str
    time_based: bool
    error: bool

# ------------------------
# Encoding / Decoding Tests
# ------------------------

@pytest.mark.parametrize("data", [
    (1, 2, 3),
    [1, 2, (3, 4)],
    {"a": (1, 2), "b": [3, 4]},
    {"nested": [{"x": (1, {"y": [2, 3]})}]},
    "simple string",
    42,
    3.14,
    None,
    [],
    {},
    ()
])
def test_encode_decode_round_trip(data: object) -> None:
    """
    Test _encode and _decode functions that encoding and then decoding an object returns
    the original object.

    Args:
        data (object): Arbitrary data to encode and decode.
    """
    encoded = _encode(data)
    decoded = _decode(encoded)
    assert decoded == data

def test_encode_tuple_structure() -> None:
    """
    Test _encode function that encoding a tuple produces the expected dictionary 
    structure.
    """
    data = (1, 2)
    encoded = _encode(data)
    assert isinstance(encoded, dict)
    assert encoded == {"__tuple__": True, "items": [1, 2]}

def test_decode_tuple_structure() -> None:
    """
    Test _decode function that decoding a tuple-encoded dictionary returns the original 
    tuple.
    """
    encoded = {"__tuple__": True, "items": [1, 2]}
    decoded = _decode(encoded)
    assert decoded == (1, 2)

def test_nested_mixed_structure() -> None:
    """
    Test _encode and _decode for encoding and decoding of nested and mixed data 
    structures.
    """
    data = {
        "key": [
            123,
            {"subkey": (4, 5, [6, {"deep": (7,)}])}
        ]
    }
    encoded = _encode(data)
    decoded = _decode(encoded)
    assert decoded == data

# ------------------------
# Serialization Tests
# ------------------------

def test_serialize_deserialize_round_trip() -> None:
    """
    Test _serialize_styles and _deserialize_styles that serializing and then 
    deserializing a style returns the original style.
    """
    style = make_test_style()
    styles = {"Default": style}

    serialized = _serialize_styles(styles)
    deserialized = _deserialize_styles(serialized)

    assert isinstance(deserialized["Default"], pysubs2.SSAStyle)
    for key, value in style.__dict__.items():
        if isinstance(value, pysubs2.Color):
            assert getattr(deserialized["Default"], key) == value
        else:
            assert getattr(deserialized["Default"], key) == value

def test_colors_are_serialized_as_ints() -> None:
    """
    Test _serialize_styles function that color fields in serialized styles are stored 
    as integers.
    """
    style = make_test_style()
    styles = {"Default": style}

    serialized = _serialize_styles(styles)
    for key, value in serialized["Default"].items():
        if key.lower().endswith("color"):
            assert isinstance(value, int)

def test_alignment_is_preserved() -> None:
    """
    Test _serialize_styles and _deserialize_styles functions that alignment field is 
    preserved through serialization and deserialization.
    """
    style = make_test_style()
    styles = {"Default": style}

    serialized = _serialize_styles(styles)
    deserialized = _deserialize_styles(serialized)
    assert deserialized["Default"].alignment == style.alignment

# ------------------------
# Sub Processing Tests
# ------------------------

@pytest.mark.parametrize(
    'case',
    cast(list[SubProcessingTest], load_test_cases(DATA_SUB_PROCESSING))
)
@pytest.mark.parametrize('retain_newline', [True, False])
def test_sub_processing(case: SubProcessingTest, retain_newline: bool) -> None:
    """
    Test _sub_processing function for sub processing with line breaks removed and 
    retained.

    Args:
        case (SubProcessingTest): Test case data loaded from YAML.
    """
    expected_text = case['expected'] if not retain_newline else case['text']
    sub = SubtitleField(
        primary_text=case['text'],
        secondary_text=case['text']
    )
    text_p, text_s = _sub_processing(sub, retain_newline)
    assert text_p == expected_text
    assert text_s == expected_text

# ------------------------
# File Format Tests
# ------------------------

@pytest.mark.parametrize(
    'case',
    cast(list[GetFormatNameTest], load_test_cases(DATA_GET_FORMAT_NAME))
)
def test_get_format_name(case: GetFormatNameTest) -> None:
    """
    Test _get_format_name function for file format name extraction utility.

    Args:
        case (GetFormatNameTest): Test case data loaded from YAML.
    """
    assert _get_format_name(case["input"]) == case["expected"]

@pytest.mark.parametrize(
    'case',
    cast(list[ExtensionTypeTest], load_test_cases(DATA_EXT_TYPE))
)
def test_extension_type(case: ExtensionTypeTest) -> None:
    """
    Test _extension_type function for file extension type detection utility.

    Args:
        case (ExtensionTypeTest): Test case data loaded from YAML.
    """
    ext_type, error = _extension_type(case['input'])
    assert ext_type == case["time_based"]
    assert error == case["error"]

# ------------------------
# Style Name Conflict Resolution Tests
# ------------------------

def test_rename_common_styles() -> None:
    """
    Test _rename_common_styles function for renaming of common style names between 
    primary and secondary styles.
    """
    primary = make_ssafile_with_styles(["Default", "Narration"])
    secondary = make_ssafile_with_styles(["Default", "Comment"])
    updated_secondary, replacements = _rename_common_styles(primary, secondary)

    assert updated_secondary.styles.keys() == {"Default_1", "Comment"}
    assert "Default" not in updated_secondary.styles
    assert replacements == {"Default": "Default_1"}

def test_no_common_styles() -> None:
    """
    Test _rename_common_styles function that no renaming occurs when there are no 
    common style names.
    """
    primary = make_ssafile_with_styles(["Title"])
    secondary = make_ssafile_with_styles(["Comment"])
    updated_secondary, replacements = _rename_common_styles(primary, secondary)

    assert updated_secondary.styles.keys() == {"Comment"}
    assert not replacements

# ----------------------------
# Helper functions
# ----------------------------

def make_test_style() -> pysubs2.SSAStyle:
    """
    Helper to create a test SSAStyle object with preset values.

    Returns:
        pysubs2.SSAStyle: A test style object.
    """
    return pysubs2.SSAStyle(
        fontname="Arial",
        fontsize=24,
        primarycolor=pysubs2.Color(255, 0, 0, 255),
        secondarycolor=pysubs2.Color(0, 255, 0, 255),
        outlinecolor=pysubs2.Color(0, 0, 255, 255),
        backcolor=pysubs2.Color(255, 255, 255, 0),
        alignment=pysubs2.Alignment.BOTTOM_CENTER,
    )

def make_ssafile_with_styles(style_names: list[str]) -> pysubs2.SSAFile:
    """
    Helper to create an SSAFile with the given style names.

    Args:
        style_names (list[str]): List of style names to add.

    Returns:
        pysubs2.SSAFile: SSAFile with the specified styles.
    """
    subs = pysubs2.SSAFile()
    subs.styles.clear()
    for name in style_names:
        subs.styles[name] = pysubs2.SSAStyle()
    return subs
