"""Metric calculation engine for design quality assessment.

This module provides deterministic scoring functions for accessibility, layout
symmetry, and color harmony. All functions are pure with no side effects.

Functions:
    calculate_accessibility_score(html_content: str) -> int
    calculate_symmetry_score(html_content: str, regions: dict) -> int
    calculate_harmony_score(html_content: str, extracted_colors: dict) -> int

Helper functions (internal use):
    parse_color(color_str: str) -> tuple
    srgb_to_linear(channel_value: int) -> float
    relative_luminance(r: int, g: int, b: int) -> float
    contrast_ratio(rgb1: tuple, rgb2: tuple) -> float
"""

import re
import math
import colorsys
from html.parser import HTMLParser
from typing import Optional, Dict, Any, List, Tuple


# ============================================================================
# Helper Functions (Internal)
# ============================================================================


def parse_color(color_str: str) -> Tuple[int, int, int]:
    """Parse CSS color string to (r, g, b) tuple.

    Supports:
    - rgb(r, g, b) format
    - #RRGGBB format
    - #RGB format

    Args:
        color_str: CSS color string (e.g., "rgb(255, 0, 0)" or "#FF0000")

    Returns:
        Tuple (r, g, b) with values in [0, 255]
        Returns (128, 128, 128) if color cannot be parsed
    """
    # rgb(r, g, b) format
    rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_str)
    if rgb_match:
        return (int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3)))

    # #RRGGBB format
    hex_match = re.match(r'#([0-9a-fA-F]{6})', color_str)
    if hex_match:
        hex_val = hex_match.group(1)
        return (int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16))

    # #RGB format
    hex3_match = re.match(r'#([0-9a-fA-F]{3})', color_str)
    if hex3_match:
        r, g, b = hex3_match.group(1)
        return (int(r+r, 16), int(g+g, 16), int(b+b, 16))

    # Unparseable: return gray default
    return (128, 128, 128)


def srgb_to_linear(channel_value: int) -> float:
    """Convert sRGB 8-bit [0-255] to linear RGB [0-1].

    Args:
        channel_value: int in [0, 255]

    Returns:
        float in [0, 1]
    """
    srgb_normalized = channel_value / 255.0
    if srgb_normalized <= 0.03928:
        return srgb_normalized / 12.92
    else:
        return ((srgb_normalized + 0.055) / 1.055) ** 2.4


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate WCAG 2.1 relative luminance.

    Args:
        r, g, b: RGB values in [0, 255]

    Returns:
        Luminance in [0, 1]
    """
    R = srgb_to_linear(r)
    G = srgb_to_linear(g)
    B = srgb_to_linear(b)
    return 0.2126 * R + 0.7152 * G + 0.0722 * B


def contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """Calculate WCAG 2.1 contrast ratio.

    Args:
        rgb1, rgb2: tuples (r, g, b) in [0, 255]

    Returns:
        Contrast ratio (1.0 to 21.0)
    """
    L1 = relative_luminance(*rgb1)
    L2 = relative_luminance(*rgb2)
    L_lighter = max(L1, L2)
    L_darker = min(L1, L2)
    return (L_lighter + 0.05) / (L_darker + 0.05)


# ============================================================================
# Metric Functions
# ============================================================================


def calculate_accessibility_score(html_content: str) -> int:
    """Calculate WCAG 2.1 AA accessibility compliance score.

    Evaluates:
    1. Color contrast ratios (WCAG AA minimum 4.5:1 for normal text)
    2. Semantic HTML structure (penalty for div-only layouts)
    3. Touch target sizing via padding (heuristic: >= 10px)

    Args:
        html_content: Complete HTML string with embedded CSS in <style> tag

    Returns:
        Integer score in [0, 100]
        - 100: Perfect accessibility (all regions meet WCAG AA)
        - 85-99: Excellent (minor issues)
        - 70-84: Good (some issues)
        - 50-69: Fair (multiple issues)
        - 0-49: Poor (major accessibility violations)

        Returns 50 (baseline) if html_content is invalid or unparseable.

    Limitations:
        - This is a heuristic approximation without browser rendering
        - Padding >= 10px is used as proxy for 44x44px touch targets
        - Only validates rgb() and #hex colors (not named colors or hsl)
    """
    # Input validation
    if not html_content or not isinstance(html_content, str):
        return 50
    if len(html_content) < 50:  # Clearly malformed HTML
        return 50

    # Extract CSS from <style> tag
    style_match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
    if not style_match:
        return 50  # No CSS found

    css_content = style_match.group(1)

    # Track metrics
    passing_regions = 0
    total_regions = 0
    padding_bonus = 0

    # Check each region for contrast and padding
    for region_name in ['header', 'sidebar', 'content', 'footer']:
        pattern = rf'\.{region_name}\s*\{{([^}}]+)\}}'
        match = re.search(pattern, css_content)
        if not match:
            continue  # Region not in CSS (not detected)

        total_regions += 1
        css_block = match.group(1)

        # Extract background-color (last occurrence)
        bg_matches = re.findall(r'background-color:\s*(rgb\([^)]+\)|#[0-9a-fA-F]{3,6})', css_block)
        background_color = parse_color(bg_matches[-1]) if bg_matches else (255, 255, 255)

        # Extract text color (last occurrence)
        text_matches = re.findall(r'color:\s*(rgb\([^)]+\)|#[0-9a-fA-F]{3,6})', css_block)
        text_color = parse_color(text_matches[-1]) if text_matches else (0, 0, 0)

        # Calculate contrast ratio
        ratio = contrast_ratio(background_color, text_color)
        if ratio >= 4.5:
            passing_regions += 1

        # Extract padding
        padding_match = re.search(r'padding:\s*(\d+)px', css_block)
        if padding_match and int(padding_match.group(1)) >= 10:
            padding_bonus += 5

    # Semantic structure detection
    has_semantic_header = '<header' in html_content
    has_semantic_main = '<main' in html_content
    has_semantic_footer = '<footer' in html_content

    semantic_count = sum([has_semantic_header, has_semantic_main, has_semantic_footer])

    if semantic_count >= 2:
        semantic_bonus = 15  # Good semantic structure
    elif semantic_count == 1:
        semantic_bonus = 7   # Some semantic tags
    else:
        semantic_bonus = 0   # Div-only layout (no penalty, baseline)

    # Calculate base score
    if total_regions > 0:
        base_score = (passing_regions / total_regions) * 70
    else:
        base_score = 50

    # Final score
    final_score = base_score + semantic_bonus + padding_bonus
    return int(min(max(final_score, 0), 100))


def calculate_symmetry_score(html_content: str, regions: Dict[str, Optional[Dict[str, int]]]) -> int:
    """Calculate layout symmetry and visual balance score.

    Evaluates:
    1. Header/footer aspect ratio consistency
    2. Sidebar width proportionality (ideal: 25% of total width)
    3. Flexbox layout properties (flex-direction, justify-content, align-items)

    Args:
        html_content: Complete HTML string with embedded CSS
        regions: Dict from detect_layout_regions() with keys:
                 'header', 'sidebar', 'content', 'footer'
                 Each value is None or {'x', 'y', 'width', 'height'}

    Returns:
        Integer score in [0, 100]
        - 100: Perfect symmetry (all dimensions balanced)
        - 85-99: Excellent symmetry (< 5% variance)
        - 70-84: Good symmetry (< 15% variance)
        - 50-69: Fair symmetry (noticeable imbalance)
        - 0-49: Poor symmetry (major imbalance)

        Returns 50 (baseline) if regions is None/invalid or no regions detected.

    Algorithm:
        1. Validate inputs; return 50 if invalid
        2. Calculate aspect ratio variance (header vs footer):
           - If both exist: variance = |aspect_h - aspect_f| / max(aspect_h, aspect_f)
           - Award 50 pts * (1 - variance) where variance in [0, 1]
        3. Calculate sidebar width consistency:
           - If sidebar and content exist:
             * ideal_ratio = 0.25 (25% sidebar, 75% content)
             * actual_ratio = sidebar.width / (sidebar.width + content.width)
             * consistency = 1 - |actual_ratio - ideal_ratio| / ideal_ratio
             * Award 30 pts * consistency
        4. Validate flexbox properties from CSS:
           - Award 10 pts if flex-direction matches layout
           - Award 5 pts if justify-content is center/space-between
           - Award 5 pts if align-items is center
        5. Sum scores and clamp to [0, 100]
    """
    # Input validation
    if regions is None or not isinstance(regions, dict):
        return 50
    if not any(v is not None for v in regions.values()):
        return 50  # No regions detected

    variance_score = 0.0
    consistency_score = 0.0
    flexbox_score = 0.0

    # 2. Aspect ratio variance (50 pts max)
    header = regions.get('header')
    footer = regions.get('footer')

    if header is not None and footer is not None:
        if header['height'] > 0 and footer['height'] > 0:
            aspect_h = header['width'] / header['height']
            aspect_f = footer['width'] / footer['height']
            max_aspect = max(aspect_h, aspect_f)
            if max_aspect > 0:
                variance = abs(aspect_h - aspect_f) / max_aspect
                variance_score = 50 * (1 - min(variance, 1.0))
            else:
                variance_score = 50
        else:
            variance_score = 50
    else:
        variance_score = 50  # Baseline if missing

    # 3. Sidebar width consistency (30 pts max)
    sidebar = regions.get('sidebar')
    content = regions.get('content')

    if sidebar is not None and content is not None:
        total_width = sidebar['width'] + content['width']
        if total_width > 0:
            actual_ratio = sidebar['width'] / total_width
            ideal_ratio = 0.25
            deviation = abs(actual_ratio - ideal_ratio) / ideal_ratio
            consistency = 1 - min(deviation, 1.0)
            consistency_score = 30 * consistency
        else:
            consistency_score = 30
    else:
        consistency_score = 30  # Baseline if missing

    # 4. Flexbox validation (20 pts max)
    style_match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
    if style_match:
        css_content = style_match.group(1)

        # Extract .main flexbox properties
        main_match = re.search(r'\.main\s*\{([^}]+)\}', css_content)
        if main_match:
            main_css = main_match.group(1)

            # Check flex-direction (10 pts)
            has_sidebar = regions.get('sidebar') is not None
            expected_direction = 'row' if has_sidebar else 'column'
            if f'flex-direction: {expected_direction}' in main_css:
                flexbox_score += 10

            # Check justify-content (5 pts)
            if re.search(r'justify-content:\s*(center|space-between)', main_css):
                flexbox_score += 5

            # Check align-items (5 pts)
            if 'align-items: center' in main_css:
                flexbox_score += 5

    # Sum scores and clamp to [0, 100]
    total_score = variance_score + consistency_score + flexbox_score
    return int(min(max(total_score, 0), 100))


def calculate_harmony_score(html_content: str, extracted_colors: Dict[str, List[Tuple[int, int, int]]]) -> int:
    """Calculate color palette harmony and cohesion score.

    Evaluates:
    1. Hue distribution entropy (Shannon entropy in 12 bins of 30° each)
    2. Saturation consistency across colors
    3. Minimum hue spacing (avoid clustered hues)

    Args:
        html_content: Complete HTML string with embedded CSS
        extracted_colors: Dict from extract_colors() with keys:
                          'header', 'sidebar', 'content', 'footer'
                          Each value is list of 3 RGB tuples: [(r,g,b), ...]

    Returns:
        Integer score in [0, 100]
        - 100: Perfect harmony (entropy > 2.5 bits, good spacing)
        - 85-99: Excellent harmony (entropy > 2.3 bits)
        - 70-84: Good harmony (entropy > 2.0 bits)
        - 50-69: Fair harmony (entropy > 1.5 bits)
        - 0-49: Poor harmony (low entropy, monochromatic)

        Returns 50 (baseline) if extracted_colors is None/empty.
    """
    # Input validation
    if extracted_colors is None or len(extracted_colors) == 0:
        return 50

    # Aggregate all valid RGB colors
    all_colors = []
    for region_name, color_list in extracted_colors.items():
        if color_list is None or not isinstance(color_list, (list, tuple)):
            continue
        for color in color_list:
            if not isinstance(color, (tuple, list)) or len(color) != 3:
                continue
            try:
                r, g, b = int(color[0]), int(color[1]), int(color[2])
                if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                    all_colors.append((r, g, b))
            except (ValueError, TypeError):
                continue

    if len(all_colors) == 0:
        return 50  # No valid colors

    # RGB to HSV conversion
    hues = []
    saturations = []

    for r, g, b in all_colors:
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        hue_degrees = h * 360
        saturation_percent = s * 100
        hues.append(hue_degrees)
        saturations.append(saturation_percent)

    # Hue entropy calculation (50 pts max)
    bins = [0] * 12
    for hue in hues:
        bin_index = int(hue / 30) % 12
        bins[bin_index] += 1

    # Calculate Shannon entropy
    total = sum(bins)
    entropy = 0.0
    for count in bins:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    # Score: entropy / log2(12) * 70 (max entropy 3.58 → 70 pts)
    log2_12 = math.log2(12)  # ≈ 3.58
    entropy_score = (entropy / log2_12) * 70
    entropy_score = min(entropy_score, 70)

    # Saturation consistency (30 pts max)
    try:
        import numpy as np
        saturation_mean = np.mean(saturations)
        saturation_std = np.std(saturations)
    except ImportError:
        # Fallback without numpy
        saturation_mean = sum(saturations) / len(saturations)
        saturation_std = math.sqrt(sum((x - saturation_mean) ** 2 for x in saturations) / len(saturations))

    # consistency = 1 - (std / 50), clamped to [0, 1]
    consistency = 1 - (saturation_std / 50)
    consistency = max(0, min(consistency, 1))

    consistency_score = consistency * 30

    # Hue spacing (20 pts max)
    if len(hues) < 2:
        spacing_score = 20  # Single hue: neutral score
    else:
        sorted_hues = sorted(hues)
        min_spacing = 360  # Max possible

        # Check consecutive hues
        for i in range(len(sorted_hues) - 1):
            spacing = sorted_hues[i + 1] - sorted_hues[i]
            min_spacing = min(min_spacing, spacing)

        # Check wrap-around (last to first)
        wrap_spacing = (sorted_hues[0] + 360) - sorted_hues[-1]
        min_spacing = min(min_spacing, wrap_spacing)

        # Score: 20 if spacing > 30°, else proportional
        spacing_score = 20 if min_spacing > 30 else (min_spacing / 30) * 20

    # Final score
    total_score = entropy_score + consistency_score + spacing_score
    return int(min(max(total_score, 0), 100))
