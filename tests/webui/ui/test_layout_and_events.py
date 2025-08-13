
"""
End-to-end Playwright and pytest tests for DuoSubs web UI layout and event logic.

Tests merging workflow, UI state, file export options, and output correctness.
"""

import fnmatch
import multiprocessing
import random
import time
import zipfile
from pathlib import Path
from typing import Generator

import pysubs2
import pytest
from playwright.sync_api import Browser, Page, expect, sync_playwright

from duosubs import SubtitleFormat
from duosubs.webui.ui.layout import create_main_gr_blocks_ui
from tests.webui.common_utils.utils import get_free_port, wait_for_server

SUB_PATH = Path(__file__).parent / "data"
SUB_1 = SUB_PATH / "primary.srt"
SUB_2 = SUB_PATH / "secondary.srt"
EMPTY_SUB = SUB_PATH / "empty_sub.ass"
MERGED_SUB_WITH_NEWLINES = SUB_PATH / "retain_newlines.ass"
MERGED_SUB_WITHOUT_NEWLINES = SUB_PATH / "merged.ass"
MERGED_SUB_WITH_SECONDARY_ABOVE = SUB_PATH / "secondary_above_primary.ass"
MERGED_SUB_WITH_PRIMARY_ABOVE = SUB_PATH / "merged.ass"
SUB_EXT_LIST: list[str] = [f.value for f in SubtitleFormat]

# === Fixture: Reuse server session ===
@pytest.fixture(scope="session", autouse=True)
def gradio_server() -> Generator[str, None, None]:
    """
    Pytest fixture to start and yield a Gradio server URL for the test session.

    Yields:
        str: The base URL of the running Gradio server.
    """
    port = get_free_port()
    
    try:
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass

    proc = multiprocessing.Process(target=run_gradio_web_ui, args=(port,), daemon=True)
    proc.start()
    try:
        wait_for_server(f"http://127.0.0.1:{port}/", timeout=30)
        yield f"http://127.0.0.1:{port}"
    finally:
        proc.terminate()
        proc.join()

# === Fixture: Reuse browser session ===
@pytest.fixture(scope="session")
def playwright_browser() -> Generator[Browser, None, None]:
    """
    Pytest fixture to launch and yield a Playwright browser for the test session.

    Yields:
        Browser: The Playwright browser instance.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

# === Fixture: New page per test ===
@pytest.fixture()
def page(
    gradio_server: str,
    playwright_browser: Browser
) -> Generator[Page, None, None]:
    """
    Pytest fixture to create and yield a new Playwright page for each test.

    Args:
        gradio_server: The base URL of the running Gradio server.
        playwright_browser: The Playwright browser instance.

    Yields:
        Page: The Playwright page instance for the test.
    """
    context = playwright_browser.new_context()
    page = context.new_page()
    page.goto(gradio_server)
    yield page
    context.close()

# ---------------------------------
# Basic Merging Workflow Tests
# ---------------------------------

def test_initial_button_states(page: Page) -> None:
    """
    Test that the initial state of Merge and Cancel buttons is correct.

    By default, Merge should be enabled and Cancel should be disabled, before any 
    merging is initiated.

    Args:
        page (Page): Playwright page instance.
    """
    merge_button = page.get_by_role("button", name="Merge")
    cancel_button = page.get_by_role("button", name="Cancel")

    merge_button.wait_for()
    cancel_button.wait_for()

    assert merge_button.is_enabled()
    assert cancel_button.is_disabled()

def test_empty_subtitles(page: Page) -> None:
    """
    Test merging with empty subtitles triggers an error toast.

    Args:
        page (Page): Playwright page instance.
    """
    perform_merging(page, EMPTY_SUB, EMPTY_SUB)

    expect(
        page.locator("div.toast-body.error").filter(has_text="is empty.")
    ).to_be_visible(timeout=10000)

def test_start_merge(page: Page, tmp_path: Path) -> None:
    """
    Test the full merging workflow and ensure the correctness of output file downloaded.

    Args:
        page (Page): Playwright page instance.
        tmp_path (Path): Temporary path for output files.
    """
    perform_merging(page, SUB_1, SUB_2)

    merge_button = page.get_by_role("button", name="Merge")
    cancel_button = page.get_by_role("button", name="Cancel")

    expect(merge_button).to_be_disabled()
    expect(cancel_button).to_be_enabled()

    perform_download(page, tmp_path / "output.zip")

    expect(merge_button).to_be_enabled()
    expect(cancel_button).to_be_disabled()

    ending_naming_and_format = [
        "_combined.ass",
        "_primary.ass",
        "_secondary.ass"
    ]

    assert_merged_subs_naming(tmp_path / "output.zip", ending_naming_and_format)

def test_cancel_merge(page: Page) -> None:
    """
    Test that cancelling the merge process updates UI state and ensures no download is 
    available.

    Args:
        page (Page): Playwright page instance.
    """
    perform_merging(page, SUB_1, SUB_2)

    merge_button = page.get_by_role("button", name="Merge")
    cancel_button = page.get_by_role("button", name="Cancel")

    expect(merge_button).to_be_disabled()
    expect(cancel_button).to_be_enabled()

    cancel_button.click()

    expect(page.get_by_text(
        "The merging process is stopped.",
        exact=True)
    ).to_be_visible(timeout=20000)

    download_section = page.get_by_text(
        "Processed Subtitles (in zip)",
        exact=True
    ).locator("..")
    download_link = download_section.locator("a[download]")

    expect(download_link).not_to_be_visible()
    expect(merge_button).to_be_enabled()
    expect(cancel_button).to_be_disabled()

    assert download_link.count() == 0

# ----------------------------
# Merging Options Tests
# ----------------------------

@pytest.mark.parametrize(
    "enable_option, expected_merged_subs",
    [
        (True, MERGED_SUB_WITH_NEWLINES),
        (False, MERGED_SUB_WITHOUT_NEWLINES)
    ]
)
def test_retain_newlines_option(
    page: Page,
    tmp_path: Path,
    enable_option: bool,
    expected_merged_subs: Path
) -> None:
    """
    Test the correctness of retain newlines options in the merged subtitle output.

    Args:
        page (Page): Playwright page instance.
        tmp_path (Path): Temporary path for output files.
        enable_option (bool): Whether to enable the retain newlines option.
        expected_merged_subs (Path): Path to expected merged subtitle file.
    """
    page.get_by_role("tab", name="Output Styling").click()
    retain_newline_option = page.get_by_role("checkbox", name="Retain Newlines")

    if enable_option:
        retain_newline_option.check()
    else:
        retain_newline_option.uncheck()

    perform_merging(page, SUB_1, SUB_2)
    perform_download(page, tmp_path / "output.zip")
    assert_merged_subs_content(tmp_path / "output.zip", expected_merged_subs)

@pytest.mark.parametrize(
    "enable_option, expected_merged_subs",
    [
        (True, MERGED_SUB_WITH_SECONDARY_ABOVE),
        (False, MERGED_SUB_WITH_PRIMARY_ABOVE)
    ]
)
def test_secondary_above_primary_options(
    page: Page,
    tmp_path: Path,
    enable_option: bool,
    expected_merged_subs: Path
) -> None:
    """
    Test the correctness of secondary above primary options on merged subtitle output.

    Args:
        page (Page): Playwright page instance.
        tmp_path (Path): Temporary path for output files.
        enable_option (bool): Whether to enable the secondary above primary option.
        expected_merged_subs (Path): Path to expected merged subtitle file.
    """
    page.get_by_role("tab", name="Output Styling").click()
    secondary_above_primary_option = page.get_by_role(
        "checkbox",
        name="Secondary subtitle above primary subtitle"
    )

    if enable_option:
        secondary_above_primary_option.check()
    else:
        secondary_above_primary_option.uncheck()

    perform_merging(page, SUB_1, SUB_2)
    perform_download(page, tmp_path / "output.zip")
    assert_merged_subs_content(tmp_path / "output.zip", expected_merged_subs)

@pytest.mark.parametrize(
    "excluded_file_types, naming_list",
    [
        (
            ["Combined"], 
            ["_primary.ass","_secondary.ass"]
        ),
        (
            ["Primary"], 
            ["_combined.ass","_secondary.ass"]
        ),
        (
            ["Secondary"], 
            ["_combined.ass","_primary.ass"]
        ),
    ]
)
def test_excluding_subs_file(
    page: Page,
    tmp_path: Path,
    excluded_file_types: list[str],
    naming_list: list[str]
) -> None:
    """
    Test the correctness of excluding subtitle file types from the output ZIP.

    Args:
        page (Page): Playwright page instance.
        tmp_path (Path): Temporary path for output files.
        excluded_file_types (list[str]): List of subtitle file types to exclude.
        naming_list (list[str]): List of expected output file name endings.
    """
    page.get_by_role("tab", name="File Exports").click()
    for file_type in excluded_file_types:
        page.get_by_role("checkbox", name=file_type).check()

    perform_merging(page, SUB_1, SUB_2)
    perform_download(page, tmp_path / "output.zip")
    assert_merged_subs_naming(tmp_path / "output.zip", naming_list)

def test_format_options(page: Page, tmp_path: Path) -> None:
    """
    Test that changing subtitle format options affects output file naming.

    Args:
        page (Page): Playwright page instance.
        tmp_path (Path): Temporary path for output files.
    """
    random_format = []
    for _ in range(3):
        random_format.append(SUB_EXT_LIST[random.randint(0,len(SUB_EXT_LIST)-1)])

    page.get_by_role("tab", name="File Exports").click()

    page.get_by_role("listbox", name="Combined").click()
    page.get_by_role("option", name=random_format[0]).nth(0).click()

    page.get_by_role("listbox", name="Primary").click()
    page.get_by_role("option", name=random_format[1]).nth(0).click()

    page.get_by_role("listbox", name="Secondary").click()
    page.get_by_role("option", name=random_format[2]).nth(0).click()

    naming_list = [
        f"_combined.{random_format[0]}",
        f"_primary.{random_format[1]}",
        f"_secondary.{random_format[2]}"
    ]

    perform_merging(page, SUB_1, SUB_2)
    perform_download(page, tmp_path / "output.zip")
    assert_merged_subs_naming(tmp_path / "output.zip", naming_list)

def test_omit_all_subs_files(page: Page) -> None:
    """
    Test that omitting all subtitle files triggers a warning and disables merging and 
    download process.

    Args:
        page (Page): Playwright page instance.
    """
    page.get_by_role("tab", name="File Exports").click()
    page.get_by_role("checkbox", name="Combined").wait_for()
    checkboxes = page.get_by_role("checkbox")
    count = checkboxes.count()

    for i in range(count):
        checkboxes.nth(i).check()

    expect(
        page.locator("div.toast-body.warning").filter(has_text="Nothing to merge")
    ).to_be_visible(timeout=10000)

    time.sleep(10)

    perform_merging(page, SUB_1, SUB_2)

    expect(
        page.locator("div.toast-body.warning").filter(has_text="Nothing to merge")
    ).to_be_visible(timeout=10000)

    section = page.get_by_text(
        "Processed Subtitles (in zip)",
        exact=True
    ).locator("..")
    download_link = section.locator("a[download]")

    assert download_link.count() == 0

# ----------------------------
# Helper functions
# ----------------------------

def run_gradio_web_ui(port: int) -> None:
    """
    Helper to start the Gradio web UI server on a given port.

    Args:
        port (int): Port to run the server on.
    """
    duosubs_server = create_main_gr_blocks_ui()
    duosubs_server.queue(default_concurrency_limit=None)
    duosubs_server.launch(server_port=port)

def perform_merging(page: Page, sub_1: Path, sub_2: Path) -> None:
    """
    Helper to perform the merging workflow in the UI, starting from file upload to 
    clicking the Merge button.

    Args:
        page (Page): Playwright page instance.
        sub_1 (Path): Path to primary subtitle file.
        sub_2 (Path): Path to secondary subtitle file.
    """
    page.get_by_role("tab", name="Model & Device").click()
    page.get_by_label(
        "Sentence Transformer Model"
    ).fill("sentence-transformers/all-MiniLM-L6-v2")

    page.locator(
        "div:has-text('Primary Subtitle File') input[type='file']"
    ).nth(0).set_input_files(sub_1)
    page.locator(
        "div:has-text('Secondary Subtitle File') input[type='file']"
    ).nth(0).set_input_files(sub_2)

    page.get_by_role("button", name="Merge").click()

def perform_download(page: Page, output_zip_path: Path) -> None:
    """
    Helper to download the merged output ZIP file from the UI.

    Args:
        page (Page): Playwright page instance.
        output_zip_path (Path): Path to save the downloaded ZIP file.
    """
    section = page.get_by_text(
        "Processed Subtitles (in zip)",
        exact=True
    ).locator("..")
    download_link = section.locator("a[download]")

    with page.expect_download() as download_info:
        download_link.click()
    download_info.value.save_as(output_zip_path)

def assert_merged_subs_naming(output_zip_path: Path, naming_list: list[str]) -> None:
    """
    Assert that the output ZIP contains files with the expected naming.

    Args:
        output_zip_path (Path): Path to the output ZIP file.
        naming_list (list[str]): List of expected file name endings.
    """
    with zipfile.ZipFile(output_zip_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        assert len(file_list) == len(naming_list)
        for naming in naming_list:
            assert any(f.endswith(naming) for f in file_list)

def assert_merged_subs_content(output_zip_path: Path, expected_subs_path: Path) -> None:
    """
    Assert that the merged subtitle content matches the expected file.

    Args:
        output_zip_path (Path): Path to the output ZIP file.
        expected_subs_path (Path): Path to the expected subtitle file.
    """
    with zipfile.ZipFile(output_zip_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        assert any(f.endswith("_combined.ass") for f in file_list)
        
        combined_file_name = ""
        for name in zip_ref.namelist():
            if fnmatch.fnmatch(name, "*_combined.ass"):
                combined_file_name = name

        with zip_ref.open(combined_file_name) as f:
            merged_subs =  pysubs2.SSAFile.from_string(f.read().decode("utf-8"))
            expected_subs = pysubs2.load(str(expected_subs_path))
            for output, expected in zip(merged_subs, expected_subs, strict=False):
                assert output.start == expected.start
                assert output.end == expected.end
                assert output.text == expected.text
