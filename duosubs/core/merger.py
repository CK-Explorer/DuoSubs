"""
Subtitle merger module for aligning and merging bilingual subtitle files.

This module provides the Merger class, which uses sentence embeddings to align and 
merge primary and secondary subtitle streams.

Dependencies:
    torch: For tensor operations and similarity calculations.
    fastdtw: For Dynamic Time Warping (DTW) alignment.
    scipy: For cosine distance calculations.
    sentence_transformers: For sentence embedding models and utilities.
"""

import math
import re
from typing import Callable, Optional, cast

import numpy as np
import numpy.typing as npt
import torch
from fastdtw import fastdtw  # type: ignore
from hmmlearn import hmm  # type: ignore
from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer, util

from duosubs.subtitle.data import SubtitleData
from duosubs.subtitle.field import SubtitleField


class Merger:
    """
    A class for merging and aligning primary and secondary subtitle streams using 
    sentence embeddings.
    Provides methods for handling non-overlapping subtitle, estimating alignment and 
    refining merges.
    """
    def __init__(
            self,
            primary_subs_data: SubtitleData,
            secondary_subs_data: SubtitleData
        ) -> None:
        """
        Initializes the Merger with subtitle data and style information.

        Args:
            primary_subs_data (SubtitleData): Data for primary subtitle stream.
            secondary_subs_data (SubtitleData): Data for secondary subtitle stream.
        """
        self._primary_subs = primary_subs_data.subs
        self._primary_tokens = primary_subs_data.tokens
        self._primary_styles_tokens = primary_subs_data.styles_tokens

        self._secondary_subs = secondary_subs_data.subs
        self._secondary_tokens = secondary_subs_data.tokens
        self._secondary_styles_tokens = secondary_subs_data.styles_tokens

        self._ratio_extract_non_overlapping_subs: float = 0.02
        self._ratio_filter_and_extract_extended_version: float = 0
        self._ratio_align_subs_with_dtw: float = 0.07
        self._ratio_refined_merge: list[float] = [0.45, 0.45]
        self._ratio_eliminate_newline: float = 0.01

    def merge_subtitle(
            self,
            model: SentenceTransformer,
            stop_bit: list[bool],
            ignore_non_overlap_filter: bool = False,
            batch_size: int = 32,
            progress_callback: Optional[Callable[[int], None]] = None
        ) -> list[SubtitleField]:
        """
        Main method to merge and align subtitles using a sentence embedding model.
        First extract non-overlapping subtitles, then performs Dynamic Time Warping 
        (DTW) alignment, and finally refines subtitle merges using a sliding window 
        approach.

        Args:
            model (SentenceTransformer): The sentence embedding model.
            stop_bit (list[bool]): A flag to allow early stopping.
            ignore_non_overlap_filter (bool, optional): Flag to ignore non-overlapping 
                filter stage. Default is False.
            batch_size (int, optional): Batch size for model inference. Default is 32.
            progress_callback (Callable[[int], None], optional): Callback for progress 
                updates.

        Returns:
            list[SubtitleField]: List of merged and sorted subtitle fields after 
            complete alignment.
        """
        non_overlap_primary_subs: list[SubtitleField] = []
        non_overlap_secondary_subs: list[SubtitleField] = []
        if not ignore_non_overlap_filter:
            (
                non_overlap_primary_subs,
                non_overlap_secondary_subs
            ) = self.extract_non_overlapping_subs(stop_bit, progress_callback)

        processed_subs = self.align_subs_with_dtw(
            model,
            stop_bit,
            batch_size,
            progress_callback
        )

        stage_number = 0
        window_sizes = [3, 2]
        for window_size in window_sizes:
            processed_subs, stage_number = self.align_subs_using_neighbours(
                processed_subs,
                window_size,
                model,
                stage_number,
                stop_bit,
                batch_size,
                progress_callback
            )

        processed_subs.extend(non_overlap_primary_subs)
        processed_subs.extend(non_overlap_secondary_subs)
        processed_subs.sort()

        processed_subs = self.eliminate_unnecessary_newline(
            processed_subs,
            stop_bit,
            progress_callback
        )

        return processed_subs

    def merge_subtitle_extended_cut(
            self,
            model: SentenceTransformer,
            stop_bit: list[bool],
            batch_size: int = 32,
            progress_callback: Optional[Callable[[int], None]] = None
        ) -> list[SubtitleField]:
        """
        Merges subtitles if the primary subtitle is an extended cut version, skipping 
        non-overlapping extraction and applying additional filtering of extended cut 
        and refinement steps.

        Args:
            model (SentenceTransformer): The sentence embedding model.
            stop_bit (list[bool]): A flag to allow early stopping.
            batch_size (int, optional): Batch size for model inference. Default is 32.
            progress_callback (Callable[[int], None], optional): Callback for progress 
                updates.

        Returns:
            list[SubtitleField]: List of merged and sorted subtitle fields after 
            alignment.
        """
        self._ratio_extract_non_overlapping_subs = 0
        processed_subs = self.align_subs_with_dtw(
            model,
            stop_bit,
            batch_size,
            progress_callback
        )

        stage_number = 0
        processed_subs, stage_number = self.align_subs_using_neighbours(
            processed_subs,
            3,
            model,
            stage_number,
            stop_bit,
            batch_size,
            progress_callback
        )

        self._ratio_filter_and_extract_extended_version = 0.02
        (
            processed_subs,
            non_overlap_primary_subs
        ) = self.filter_and_extract_extended_version(
            processed_subs,
            model,
            stop_bit,
            batch_size,
            progress_callback
        )

        processed_subs, stage_number = self.align_subs_using_neighbours(
            processed_subs,
            2,
            model,
            stage_number,
            stop_bit,
            batch_size,
            progress_callback
        )
        processed_subs.extend(non_overlap_primary_subs)
        processed_subs.sort()

        processed_subs = self.eliminate_unnecessary_newline(
            processed_subs,
            stop_bit,
            progress_callback
        )

        return processed_subs

    def extract_non_overlapping_subs(
            self,
            stop_bit: list[bool],
            progress_callback: Optional[Callable[[int], None]] = None
        ) -> tuple[list[SubtitleField], list[SubtitleField]]:
        """
        Extracts non-overlapping subtitles from primary and secondary streams, and 
        delete non-overlapping subtitles from the original streams for further 
        processing.

        Args:
            stop_bit (list[bool]): A flag to allow early stopping.
            progress_callback (Callable[[int], None], optional): Callback for progress 
                updates.

        Returns:
            tuple[list[SubtitleField], list[SubtitleField]]:
            - List of non-overlapping primary subtitles.
            - List of non-overlapping secondary subtitles.
        """
        if stop_bit[0]:
            return [], []

        (
            non_overlap_primary_subs,
            non_overlap_primary_token_spans
        ) = self._filter_and_extract_non_overlap_subs(
            self._primary_subs,
            self._secondary_subs,
            True
        )
        (
            non_overlap_secondary_subs,
            non_overlap_secondary_token_spans
        ) = self._filter_and_extract_non_overlap_subs(
            self._secondary_subs,
            self._primary_subs,
            False
        )
        self._primary_subs = Merger._filter_token_spans(self._primary_subs)
        self._secondary_subs = Merger._filter_token_spans(self._secondary_subs)
        (
            self._primary_tokens,
            self._primary_styles_tokens
        ) = Merger._filter_tokens_and_styles(
            self._primary_tokens,
            self._primary_styles_tokens,
            non_overlap_primary_token_spans
        )
        (
            self._secondary_tokens,
            self._secondary_styles_tokens
        ) = Merger._filter_tokens_and_styles(
            self._secondary_tokens,
            self._secondary_styles_tokens,
            non_overlap_secondary_token_spans
        )

        if progress_callback and not stop_bit[0]:
            progress_percent = Merger._get_progress_percentage(
                0,
                1,
                self._ratio_extract_non_overlapping_subs
            )
            progress_callback(progress_percent) # incremental update

        return non_overlap_primary_subs, non_overlap_secondary_subs

    def align_subs_with_dtw(
            self,
            model: SentenceTransformer,
            stop_bit: list[bool],
            batch_size: int = 32,
            progress_callback: Optional[Callable[[int], None]] = None
        ) -> list[SubtitleField]:
        """
        Aligns subtitles using Dynamic Time Warping (DTW) based on sentence embeddings.

        Args:
            model (SentenceTransformer): The sentence embedding model.
            stop_bit (list[bool]): A flag to allow early stopping.
            batch_size (int, optional): Batch size for model inference. Default is 32.
            progress_callback (Callable[[int], None], optional): Callback for progress 
                updates.

        Returns:
            list[SubtitleField]: List of processed subtitle fields after DTW alignment.
        """
        if stop_bit[0]:
            return []

        dtw_path = self._get_dtw_path_alignment(model, batch_size)
        processed_subs = self._align_subs_with_secondary_tokens(dtw_path)

        if progress_callback and not stop_bit[0]:
            progress_percent = Merger._get_progress_percentage(
                0,
                1,
                self._ratio_align_subs_with_dtw,
                self._ratio_extract_non_overlapping_subs
            )
            progress_callback(progress_percent) # incremental update

        return processed_subs

    def align_subs_using_neighbours(
            self,
            subs: list[SubtitleField],
            subtitle_window_size: int,
            model: SentenceTransformer,
            stage_number: int,
            stop_bit: list[bool],
            batch_size: int = 32,
            progress_callback: Optional[Callable[[int], None]] = None
        ) -> tuple[list[SubtitleField], int]:
        """
        Refines the alignment of merged subtitles based on sentence similarity using a 
        sliding window of consecutive subtitle lines. Can be run in multiple stages for 
        improved accuracy.

        Args:
            subs (list[SubtitleField]): List of merged subtitles to refine.
            subtitle_window_size (int): Window size for refinement.
            model (SentenceTransformer): The sentence embedding model.
            stage_number (int): The number of refinement stage.
            stop_bit (list[bool]): A flag to allow early stopping.
            batch_size (int, optional): Batch size for model inference. Default is 32.
            progress_callback (Callable[[int], None], optional): Callback for progress 
                updates.

        Returns:
            tuple[list[SubtitleField], int]:
            - Refined sorted list of merged subtitles.
            - The updated number of refinement stage, incremented by 1.
        """
        token_start_idx = 0
        for sub_idx, _ in enumerate(subs):
            if stop_bit[0]:
                break

            if sub_idx < len(subs)-1:
                filtered_subs = subs[sub_idx:sub_idx+subtitle_window_size]

                token_spans_indices = [
                    span for sub in filtered_subs 
                    for span in sub.secondary_token_spans[:2]
                ]

                token_end_idx = max(token_spans_indices)

                primary_text_left = [filtered_subs[0].primary_text.replace("\\N", " ")]
                primary_text_right = [" ".join(
                    [sub.primary_text.replace("\\N", " ") for sub in filtered_subs[1:]]
                )]

                token_left = [
                    self._secondary_tokens[token_start_idx:i]
                    for i in range(token_start_idx, token_end_idx+1)
                ]
                token_right = [
                    self._secondary_tokens[i:token_end_idx]
                    for i in range(token_start_idx, token_end_idx+1)
                ]

                secondary_text_left = [
                    " ".join(text_lists).replace("\\N", "")
                    for text_lists in token_left
                ]
                secondary_text_right = [
                    " ".join(text_lists).replace("\\N", "")
                    for text_lists in token_right
                ]

                left_score = Merger._compute_score(
                    primary_text_left,
                    secondary_text_left,
                    model,
                    batch_size
                )
                right_score = Merger._compute_score(
                    primary_text_right,
                    secondary_text_right,
                    model,
                    batch_size
                )

                total_scores = left_score + right_score * (len(filtered_subs)-1)
                _, best_match_idx = torch.max(total_scores, dim=1)
                score_idx = int(best_match_idx.item())
                subs[sub_idx].score = left_score[0][score_idx].item()
                token_end_idx = token_start_idx + int(best_match_idx.item())
            else:
                token_end_idx = len(self._secondary_tokens)
                subs[sub_idx].score = Merger._compute_score(
                    subs[sub_idx].primary_text,
                    " ".join(
                        self._secondary_tokens[token_start_idx:token_end_idx]
                    ).replace("\\N", ""),
                    model,
                    batch_size
                ).item()

            subs[sub_idx].secondary_token_spans = (token_start_idx, token_end_idx)
            subs[sub_idx].secondary_text = " ".join(
                self._secondary_tokens[token_start_idx:token_end_idx]
            )
            subs[sub_idx].secondary_style = (
                self._secondary_styles_tokens[token_start_idx]
                if token_start_idx < len(self._secondary_styles_tokens)
                else subs[sub_idx].secondary_style
            )
            token_start_idx = token_end_idx

            if progress_callback:
                progress_percent = Merger._get_progress_percentage(
                        sub_idx,
                        len(subs),
                        self._ratio_refined_merge[stage_number],
                        self._ratio_filter_and_extract_extended_version,
                        self._ratio_extract_non_overlapping_subs,
                        self._ratio_align_subs_with_dtw,
                        *self._ratio_refined_merge[:stage_number]
                    )
                progress_callback(progress_percent) # incremental update

        stage_number += 1
        subs.sort()
        return subs, stage_number
    
    def filter_and_extract_extended_version(
            self,
            subs: list[SubtitleField],
            model: SentenceTransformer,
            stop_bit: list[bool],
            batch_size: int = 32,
            progress_callback: Optional[Callable[[int], None]] = None
        ) -> tuple[list[SubtitleField], list[SubtitleField]]:
        """
        Filters and extracts extended segments from merged subtitles.

        First, detects possible extended segments from binary mask, with 1 indicating 
        presence of secondary text, and 0 otherwise, which are further denoised by HMM.

        Then, filters out the extended segments based on the best sentence similarity, 
        by progressively deleting the extended subtitle line, starting from the middle 
        of the extended segments.

        Args:
            subs (list[SubtitleField]): List of merged subtitles to filter.
            model (SentenceTransformer): The sentence embedding model.
            stop_bit (list[bool]): A flag to allow early stopping.
            batch_size (int, optional): Batch size for model inference. Default is 32.
            progress_callback (Callable[[int], None], optional): Callback for progress 
                updates.

        Returns:
            tuple[list[SubtitleField], list[SubtitleField]]:
            - Filtered list of merged subtitles.
            - List of subtitles representing extended cut.
        """
        binary_mask = Merger._make_secondary_text_presence_mask(subs)
        clusters, _ = Merger._denoising_binary_mask_with_hmm(binary_mask)
        extended_cut_idx_spans = []

        for idx, cluster in enumerate(clusters):
            if stop_bit[0]:
                return [],[]
            
            start, end = cluster
            if end - start <= 1:
                continue

            padding = min(10, int(end - start))

            first_sub_idx = (
                max(0, start - padding)
                if idx-1 < 0
                else max(start - padding, clusters[idx-1][1])
            ) # inclusive
            last_sub_idx = (
                min(end + padding, clusters[idx+1][0])
                if idx+1 < len(clusters)
                else min(end + padding, len(subs))
            ) # exclusive

            sequence = Merger._get_sequence_list(start, end)
            filter_list = Merger._get_filter_list(sequence)

            subs_text_after_filtered = []
            for filter_span in filter_list:
                filtered_subs = (
                    subs[first_sub_idx:filter_span[0]] +
                    subs[filter_span[1]:last_sub_idx]
                )
                primary_text = " ".join(
                    [sub.primary_text.replace("\\N", " ") for sub in filtered_subs]
                )
                subs_text_after_filtered.append(primary_text)

            secondary_text = " ".join(
                self._secondary_tokens[
                    subs[first_sub_idx].secondary_token_spans[0]:
                    subs[last_sub_idx-1].secondary_token_spans[1]
                ]
            ).replace("\\N", "")

            score = Merger._compute_score(
                secondary_text,
                subs_text_after_filtered,
                model,
                batch_size
            )

            _, best_match_idx = torch.max(score, dim=1)
            score_idx = int(best_match_idx.item())
            extended_cut_idx_spans.append(filter_list[score_idx])

            if progress_callback:
                progress_percent = Merger._get_progress_percentage(
                    idx,
                    len(clusters),
                    self._ratio_filter_and_extract_extended_version,
                    self._ratio_extract_non_overlapping_subs,
                    self._ratio_align_subs_with_dtw,
                    *self._ratio_refined_merge[:1]
                )
                progress_callback(progress_percent) # incremental update

        subs, extended_cut_subs = Merger._remove_extended_segments(
            extended_cut_idx_spans,
            subs,
            self._secondary_tokens
        )

        return subs, extended_cut_subs

    def eliminate_unnecessary_newline(
            self,
            subs: list[SubtitleField],
            stop_bit: list[bool],
            progress_callback: Optional[Callable[[int], None]] = None
        ) -> list[SubtitleField]:
        """
        Cleans up unnecessary newlines in subtitle text fields.

        Args:
            subs (list[SubtitleField]): List of merged subtitles to clean.
            stop_bit (list[bool]): A flag to allow early stopping.
            progress_callback (Callable[[int], None], optional): Callback for progress 
                updates.

        Returns:
            list[SubtitleField]: Cleaned list of merged subtitles.
        """
        boundary_linebreak_pattern = re.compile(r"^(\s*\\N\s*)+|(\s*\\N\s*)+$")
        spaced_linebreak_pattern = re.compile(r"\s*\\N\s*")

        def remove_unncessary_newline(text: str) -> str:
            text = boundary_linebreak_pattern.sub("", text).strip()
            text = spaced_linebreak_pattern.sub(r"\\N", text)
            return text

        for idx, sub in enumerate(subs):
            if stop_bit[0]:
                break

            sub.primary_text = remove_unncessary_newline(sub.primary_text)
            sub.secondary_text = remove_unncessary_newline(sub.secondary_text)

            if progress_callback:
                progress_percent = Merger._get_progress_percentage(
                    idx,
                    len(subs),
                    self._ratio_eliminate_newline,
                    self._ratio_filter_and_extract_extended_version,
                    self._ratio_extract_non_overlapping_subs,
                    self._ratio_align_subs_with_dtw,
                    *self._ratio_refined_merge
                )
                progress_callback(progress_percent) # incremental update

        return subs

    def _get_dtw_path_alignment(
            self,
            model: SentenceTransformer,
            batch_size: int = 32
        ) -> list[tuple[int, int]]:
        """
        Computes the DTW path for aligning primary and secondary subtitle tokens.

        Args:
            model (SentenceTransformer): The sentence embedding model.
            batch_size (int, optional): Batch size for model inference. Default is 32.

        Returns:
            list[tuple[int, int]]: DTW path as a list of index pairs for alignment.
        """
        primary_tokens_embs = model.encode(
            self._primary_tokens,
            convert_to_tensor=True,
            batch_size=batch_size
        )
        secondary_tokens_embs = model.encode(
            self._secondary_tokens,
            convert_to_tensor=True,
            batch_size=batch_size
        )

        primary_tokens_vecs = primary_tokens_embs.cpu().numpy()
        secondary_tokens_vecs = secondary_tokens_embs.cpu().numpy()
        _, dtw_path = fastdtw(primary_tokens_vecs, secondary_tokens_vecs, dist=cosine)

        return cast(list[tuple[int, int]], dtw_path)

    def _align_subs_with_secondary_tokens(
            self,
            dtw_path: list[tuple[int, int]]
        ) -> list[SubtitleField]:
        """
        Aligns primary subtitles with secondary tokens based on the DTW path.

        Args:
            dtw_path (list[tuple[int, int]]): DTW path as a list of index pairs for 
                alignment.

        Returns:
            list[SubtitleField]: List of aligned subtitle fields.
        """
        path_idx = 0
        aligned_subs = []
        for sub in self._primary_subs:
            start, end = sub.primary_token_spans
            secondary_token_indices = []

            while start < dtw_path[path_idx][0]:
                path_idx += 1

            while path_idx < len(dtw_path) and end > dtw_path[path_idx][0]:
                secondary_token_indices.append(dtw_path[path_idx][1])
                path_idx += 1

            secondary_token_spans = (
                min(secondary_token_indices),
                max(secondary_token_indices)+1
            )
            secondary_text = " ".join(
                    self._secondary_tokens[secondary_token_spans[0]:secondary_token_spans[1]]
                )

            aligned_subs.append(
                SubtitleField(
                    start=sub.start,
                    end=sub.end,
                    primary_token_spans=sub.primary_token_spans,
                    secondary_token_spans=secondary_token_spans,
                    primary_text=sub.primary_text,
                    secondary_text=secondary_text,
                    primary_style=sub.primary_style,
                    secondary_style=self._secondary_styles_tokens[min(secondary_token_indices)]
                )
            )

        return aligned_subs

    @staticmethod
    def _filter_and_extract_non_overlap_subs(
            input_subs: list[SubtitleField],
            ref_subs: list[SubtitleField],
            input_is_primary: bool
        ) -> tuple[list[SubtitleField], list[tuple[int, int]]]:
        """
        Filters and extracts non-overlapping subtitles from the input subtitle stream.
        
        This method will remove the input subtitles that do not overlap with the 
        reference subtitle stream, and produce a list of non-overlapping subtitles and 
        their token spans.

        Args:
            input_subs (list[SubtitleField]): Input subtitle stream to filter.
            ref_subs (list[SubtitleField]): Reference subtitle stream for overlap 
                checking.
            input_is_primary (bool): Flag indicating if the input subtitles are primary.

        Returns:
            tuple[list[SubtitleField], list[tuple[int, int]]]:
            - List of non-overlapping subtitles.
            - List of token span tuples for the non-overlapping subtitles.
        """
        non_overlap_subs = []
        non_overlap_token_spans = []
        input_subs_idx = subs_ref_idx = 0

        while input_subs_idx < len(input_subs):
            while (
                subs_ref_idx < len(ref_subs)
                and ref_subs[subs_ref_idx].end <= input_subs[input_subs_idx].start
            ):
                subs_ref_idx += 1

            if not (
                subs_ref_idx < len(ref_subs)
                and ref_subs[subs_ref_idx].start < input_subs[input_subs_idx].end
                and ref_subs[subs_ref_idx].end > input_subs[input_subs_idx].start
            ):
                token_spans = input_subs[input_subs_idx].primary_token_spans
                text = input_subs[input_subs_idx].primary_text
                style = input_subs[input_subs_idx].primary_style
                non_overlap_subs.append(
                    SubtitleField(
                        start=input_subs[input_subs_idx].start,
                        end=input_subs[input_subs_idx].end,
                        primary_text=text if input_is_primary else "",
                        secondary_text="" if input_is_primary else text,
                        primary_style=style if input_is_primary else "Default",
                        secondary_style="Default" if input_is_primary else style
                    )
                )
                non_overlap_token_spans.append(token_spans)
                del input_subs[input_subs_idx]
            else:
                input_subs_idx += 1

        non_overlap_subs.sort()
        return non_overlap_subs, non_overlap_token_spans

    @staticmethod
    def _filter_token_spans(subs: list[SubtitleField]) -> list[SubtitleField]:
        """
        Adjusts the token spans of subtitles, after filtering out non-overlapping 
        subtitles.

        Args:
            subs (list[SubtitleField]): List of subtitles after filtering out 
                non-overlapping subtitles.

        Returns:
            list[SubtitleField]: List of subtitles with adjusted token spans.
        """
        start = 0
        for sub in subs:
            tokens_length = sub.primary_token_spans[1] - sub.primary_token_spans[0]
            end = start + tokens_length
            sub.primary_token_spans = (start, end)
            start = end

        return subs

    @staticmethod
    def _filter_tokens_and_styles(
            tokens: list[str],
            tokens_styles: list[str],
            non_overlap_token_spans: list[tuple[int, int]]
        ) -> tuple[list[str], list[str]]:
        """
        Filters and updates tokens and styles based on the non-overlapping token spans.

        Args:
            tokens (list[str]): List of subtitle tokens, before filtering 
                non-overlapping subtitles.
            tokens_styles (list[str]): List of corresponding token styles, before 
                filtering non-overlapping subtitles.
            non_overlap_token_spans (list[tuple[int, int]]): List of non-overlapping 
                token spans.

        Returns:
            tuple[list[str], list[str]]:
            - Updated list of tokens without non-overlapping subtitles.
            - Updated list of token styles without non-overlapping subtitles.
        """
        updated_tokens = []
        updated_tokens_styles = []
        start_previous = 0
        for token_spans in non_overlap_token_spans:
            start, end = token_spans
            updated_tokens.extend(tokens[start_previous:start])
            updated_tokens_styles.extend(tokens_styles[start_previous:start])
            start_previous = end

        updated_tokens.extend(tokens[start_previous:len(tokens)])
        updated_tokens_styles.extend(tokens_styles[start_previous:len(tokens)])

        return updated_tokens, updated_tokens_styles
    
    @staticmethod
    def _remove_extended_segments(
            extended_cut_idx_spans: list[tuple[int,int]],
            subs: list[SubtitleField],
            secondary_tokens: list[str]
        ) -> tuple[list[SubtitleField],list[SubtitleField]]:
        """
        Removes extended segments from the subtitle list and updates token spans and 
        text.

        Args:
            extended_cut_idx_spans (list[tuple[int, int]]): List of index spans for 
                extended cut.
            subs (list[SubtitleField]): List of merged subtitles.
            secondary_tokens (list[str]): List of secondary subtitle tokens.

        Returns:
            tuple[list[SubtitleField], list[SubtitleField]]:
            - Updated list of merged subtitles with extended segments removed.
            - List of subtitles representing the extended cut.
        """
        reversed_list = extended_cut_idx_spans[::-1]
        extended_cut_subs: list[SubtitleField] = []

        for idx_span in reversed_list:
            start_idx, end_idx = idx_span

            extended_cut_segments = subs[start_idx:end_idx]
            subs = subs[:start_idx] + subs[end_idx:]

            if start_idx > 0:
                token_start = subs[start_idx-1].secondary_token_spans[0]
                if start_idx != len(subs):
                    token_end = subs[start_idx].secondary_token_spans[0]
                else:
                    token_end = extended_cut_segments[-1].secondary_token_spans[1]
                subs[start_idx-1].secondary_token_spans = (token_start, token_end)
                subs[start_idx-1].secondary_text = " ".join(
                    secondary_tokens[token_start:token_end]
                )
            else:
                token_end = 0
                subs[start_idx].secondary_token_spans = (
                    token_end,
                    subs[start_idx].secondary_token_spans[1]
                )
                subs[start_idx].secondary_text = " ".join(
                    secondary_tokens[
                        token_end:subs[start_idx].secondary_token_spans[1]
                    ]
                )

            for sub in extended_cut_segments:
                sub.secondary_text = ""
                sub.score = -1
                sub.secondary_token_spans = (token_end, token_end)

            extended_cut_subs.extend(extended_cut_segments)

        return subs, extended_cut_subs
    
    @staticmethod
    def _denoising_binary_mask_with_hmm(
            binary_mask: list[int]
        ) -> tuple[list[tuple[int, int]], float | None]:
        """
        Applies HMM-based denoising to a binary mask to identify clusters of zeros.

        If the binary mask is too short (less than 5 items), it will not apply HMM-based
        denoising and cluster the binary states directly.

        Args:
            binary_mask (list[int]): Binary list representing subtitle presence.

        Returns:
            tuple[list[tuple[int, int]], float]:
            - List of clusters (start, end) where state is zero.
            - Probability of the HMM sequence.
        """
        if len(binary_mask) >= 5:
            binary_array = np.array(binary_mask).reshape(-1, 1)

            model = hmm.CategoricalHMM(n_components=2, n_iter=20, init_params="")
            model.startprob_ = np.array([0.5, 0.5])
            model.transmat_  = np.array([[0.99, 0.01],
                                        [0.01, 0.99]])
            model.emissionprob_ = np.array([[0.95, 0.05],
                                            [0.05, 0.95]])

            model.fit(binary_array)
            logprob, states = model.decode(binary_array, algorithm="viterbi")
            probability = math.exp(logprob / len(binary_array))
        else:
            states = binary_mask
            probability = None

        clusters = Merger._cluster_binary_states(states)

        return clusters, probability

    @staticmethod
    def _make_secondary_text_presence_mask(
            processed_subs: list[SubtitleField]
        ) -> list[int]:
        """
        Creates a binary list indicating the presence of secondary text in subtitles.

        Args:
            processed_subs (list[SubtitleField]): List of processed subtitles.

        Returns:
            list[int]: Binary list where 1 indicates presence of secondary text, 0 
                otherwise.
        """
        binary_mask: list[int] = []
        for sub in processed_subs:
            if sub.secondary_text:
                binary_mask.append(1)
            else:
                binary_mask.append(0)
        return binary_mask

    @staticmethod
    def _get_filter_list(sequence_filter_list: list[int]) -> list[tuple[int,int]]:
        """
        Generates a list of filter spans from a sequence list.

        Args:
            sequence_filter_list (list[int]): Sequence of indices.

        Returns:
            list[tuple[int, int]]: List of (start, end) index spans.
        """
        filter_list = []
        for idx, _ in enumerate(sequence_filter_list):
            sublist = sequence_filter_list[:idx+1]
            start = min(sublist)
            end = max(sublist)+1
            filter_list.append((start, end))
        return filter_list

    @staticmethod
    def _get_sequence_list(start: int, end: int) -> list[int]:
        """
        Generates a sequence list for filtering based on start and end indices.

        Args:
            start (int): Start index.
            end (int): End index.

        Returns:
            list[int]: Sequence of indices for filtering.
        """
        sequence_to_filter = []
        idx = start + math.ceil((end - start)/2) - 1
        for i in range(end-start):
            if i%2==0:
                idx-=i
            else:
                idx+=i
            sequence_to_filter.append(idx)
        return sequence_to_filter

    @staticmethod
    def _cluster_binary_states(
            states: npt.NDArray[np.int_] | list[int]
        ) -> list[tuple[int, int]]:
        """
        Clusters consecutive zeros in a binary state list.

        Args:
            states (npt.NDArray[np.int_] | list[int]): List or array of binary states.

        Returns:
            list[tuple[int, int]]: List of (start, end) index spans for clusters of 
                zeros.
        """
        clusters = []
        i = 0
        while i < len(states):
            if states[i] == 0:
                j = i
                while j < len(states) and states[j] == 0:
                    j += 1
                clusters.append((i, j))
                i = j
            else:
                i += 1
        return clusters

    @staticmethod
    def _compute_score(
            reference_texts: str | list[str],
            target_texts: str | list[str],
            model: SentenceTransformer,
            batch_size: int = 32
        ) -> torch.Tensor:
        """
        Computes cosine similarity scores between reference and target texts using the 
        embedding model.

        Args:
            reference_texts (str | list[str]): Reference text(s).
            target_texts (str | list[str]): Target text(s).
            model (SentenceTransformer): The sentence embedding model.
            batch_size (int, optional): Batch size for model inference. Default is 32.

        Returns:
            torch.Tensor: Cosine similarity matrix.
        """
        reference_texts_embeddings = model.encode(
            reference_texts,
            convert_to_tensor=True,
            batch_size=batch_size
        )
        target_texts_embeddings = model.encode(
            target_texts,
            convert_to_tensor=True,
            batch_size=batch_size
        )

        cos_sim_matrix = util.cos_sim(
            reference_texts_embeddings, 
            target_texts_embeddings
        )

        return cos_sim_matrix

    @staticmethod
    def _get_progress_percentage(
            idx: int,
            total_idx: int,
            ratio: float,
            *previous_ratio: float
        ) -> int:
        """
        Calculates the progress percentage for multi-stage merging operations.

        Args:
            idx (int): Current index.
            total_idx (int): Total number of items.
            ratio (float): Ratio for the current stage.
            *previous_ratio (float): Ratios for previous stages.

        Returns:
            int: Progress percentage (0-100).
        """
        progress_ratio = sum(previous_ratio) + ratio * (idx+1) / total_idx
        return int(100 * progress_ratio)
