"""HTML quality measurement metrics module.

This module provides deterministic HTML quality measurement functions for:
- DOM structure analysis (nesting depth)
- Color contrast analysis (WCAG 2.1 compliance)
- Layout balance measurement (variance-based symmetry)
- Accessibility scoring (weighted WCAG 2.1 AA criteria)

All functions parse HTML with BeautifulSoup and return values in specified ranges.
Functions are deterministic: same input HTML produces same metrics every run.
"""

import re
from html.parser import HTMLParser
from bs4 import BeautifulSoup


def extract_dom_depth(html_str: str) -> int:
    """Measure maximum nesting depth of HTML elements.

    Args:
        html_str: HTML string

    Returns:
        Integer ≥ 1 (single <html> tag = depth 1)

    Examples:
        '<html><body><div>text</div></body></html>' → 4
        '<html><body><div><div><div>text</div></div></div></body></html>' → 6

    Edge Cases:
        - Empty HTML: Return 1 (just root)
        - Malformed HTML: Parse gracefully, return depth of recovered tree
    """
    try:
        if not html_str or not html_str.strip():
            return 1

        soup = BeautifulSoup(html_str, 'html.parser')

        def get_max_depth(element, current_depth=1):
            """Recursively calculate max depth starting from element."""
            max_child_depth = current_depth
            for child in element.children:
                # Include both tag nodes and text nodes
                if isinstance(child, str):
                    # Text node - increase depth if it's not just whitespace
                    if child.strip():
                        max_child_depth = max(max_child_depth, current_depth + 1)
                elif hasattr(child, 'name') and child.name:
                    # Tag node - recurse
                    child_depth = get_max_depth(child, current_depth + 1)
                    max_child_depth = max(max_child_depth, child_depth)
            return max_child_depth

        # Start from root (html or body)
        root = soup.find('html')
        if root is None:
            root = soup.find('body')
        if root is None:
            # Try to find any tag
            for tag in soup.find_all():
                root = tag
                break

        if root is None:
            return 1

        depth = get_max_depth(root)
        return max(1, depth)

    except Exception:
        # Graceful error handling: return 1 on any parsing error
        return 1


def extract_contrast_ratios(html_str: str) -> dict[str, float]:
    """Extract WCAG contrast ratios for text/background pairs.

    Args:
        html_str: HTML string with inline styles or CSS stylesheets

    Returns:
        {'header_text_bg': 21.0, 'content_text_bg': 4.5, ...}
        All values in range [1.0, 21.0]

    WCAG Formula:
        L1, L2 = relative luminance of two colors
        contrast_ratio = (L1 + 0.05) / (L2 + 0.05) where L1 > L2

        relative_luminance = 0.2126*R + 0.7152*G + 0.0722*B
        (normalize RGB 0-255 to 0-1 first)

    Edge Cases:
        - No text or styles: Return {}
        - Invalid color: Skip element, continue
        - Malformed HTML: Parse gracefully
    """
    try:
        if not html_str or not html_str.strip():
            return {}

        soup = BeautifulSoup(html_str, 'html.parser')
        contrast_ratios = {}

        def parse_hex_color(hex_color: str) -> tuple[int, int, int] | None:
            """Parse hex color string to RGB tuple. Return None if invalid."""
            if not isinstance(hex_color, str):
                return None
            hex_color = hex_color.strip()
            if not hex_color.startswith('#'):
                return None
            hex_color = hex_color[1:]
            if len(hex_color) != 6:
                return None
            try:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b)
            except ValueError:
                return None

        def parse_rgb_color(rgb_str: str) -> tuple[int, int, int] | None:
            """Parse rgb() color string to RGB tuple. Return None if invalid."""
            if not isinstance(rgb_str, str):
                return None
            rgb_str = rgb_str.strip()
            # Match rgb(r, g, b) pattern
            match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb_str)
            if match:
                try:
                    r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    # Clamp to 0-255
                    r = max(0, min(255, r))
                    g = max(0, min(255, g))
                    b = max(0, min(255, b))
                    return (r, g, b)
                except (ValueError, AttributeError):
                    return None
            return None

        def calculate_luminance(r: int, g: int, b: int) -> float:
            """Calculate relative luminance following WCAG formula."""
            # Normalize to 0-1
            r_norm = r / 255.0
            g_norm = g / 255.0
            b_norm = b / 255.0

            # Apply gamma correction
            def gamma_correct(c: float) -> float:
                if c <= 0.03928:
                    return c / 12.92
                else:
                    return ((c + 0.055) / 1.055) ** 2.4

            r_lin = gamma_correct(r_norm)
            g_lin = gamma_correct(g_norm)
            b_lin = gamma_correct(b_norm)

            # Calculate luminance
            luminance = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
            return luminance

        def extract_color_from_style(style: str, property_name: str) -> str | None:
            """Extract color value from CSS style string (hex or rgb)."""
            if not style:
                return None
            # Match hex color: #RRGGBB
            hex_patterns = [
                rf'(?:^|;|\s)\s*{property_name}\s*:\s*(#[0-9A-Fa-f]{{6}})',  # 6-digit hex
                rf'(?:^|;|\s)\s*{property_name}\s*:\s*(#[0-9A-Fa-f]{{3}})'   # 3-digit hex
            ]
            for pattern in hex_patterns:
                match = re.search(pattern, style, re.IGNORECASE)
                if match:
                    return match.group(1)

            # Match rgb color: rgb(r, g, b)
            rgb_pattern = rf'(?:^|;|\s)\s*{property_name}\s*:\s*(rgb\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\))'
            match = re.search(rgb_pattern, style, re.IGNORECASE)
            if match:
                return match.group(1)

            return None

        # Extract CSS from style tags to build a class-to-colors mapping
        class_colors = {}
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            css_content = style_tag.string or ''
            # Extract all class definitions
            class_defs = re.findall(r'\.([a-zA-Z0-9_-]+)\s*\{([^}]*)\}', css_content)
            for class_name, css_rules in class_defs:
                bg_color = extract_color_from_style(css_rules, 'background-color')
                if not bg_color:
                    bg_color = extract_color_from_style(css_rules, 'background')
                text_color = extract_color_from_style(css_rules, 'color')

                if bg_color and text_color:
                    class_colors[class_name] = (bg_color, text_color)

        # Find elements with both text color and background color (inline styles)
        element_index = 0
        for element in soup.find_all(style=True):
            style = element.get('style', '')
            if not style:
                continue

            # Try to extract background color (support both 'background' and 'background-color')
            bg_color_str = extract_color_from_style(style, 'background-color')
            if not bg_color_str:
                bg_color_str = extract_color_from_style(style, 'background')

            text_color_str = extract_color_from_style(style, 'color')

            if not bg_color_str or not text_color_str:
                continue

            # Parse colors (support both hex and rgb)
            bg_color = parse_hex_color(bg_color_str) or parse_rgb_color(bg_color_str)
            text_color = parse_hex_color(text_color_str) or parse_rgb_color(text_color_str)

            if not bg_color or not text_color:
                continue

            # Calculate luminance for both colors
            bg_luminance = calculate_luminance(*bg_color)
            text_luminance = calculate_luminance(*text_color)

            # Ensure L1 > L2 for contrast formula
            if text_luminance > bg_luminance:
                l1, l2 = text_luminance, bg_luminance
            else:
                l1, l2 = bg_luminance, text_luminance

            # Calculate contrast ratio (avoid division by zero)
            contrast = (l1 + 0.05) / (l2 + 0.05)
            contrast = max(1.0, min(21.0, contrast))  # Clamp to [1.0, 21.0]

            # Store with a descriptive key
            key = f'element_{element_index}_text_bg'
            contrast_ratios[key] = contrast
            element_index += 1

        # Also extract from CSS-defined classes
        class_index = 0
        for class_name, (bg_color_str, text_color_str) in class_colors.items():
            # Parse colors (support both hex and rgb)
            bg_color = parse_hex_color(bg_color_str) or parse_rgb_color(bg_color_str)
            text_color = parse_hex_color(text_color_str) or parse_rgb_color(text_color_str)

            if not bg_color or not text_color:
                continue

            # Calculate luminance for both colors
            bg_luminance = calculate_luminance(*bg_color)
            text_luminance = calculate_luminance(*text_color)

            # Ensure L1 > L2 for contrast formula
            if text_luminance > bg_luminance:
                l1, l2 = text_luminance, bg_luminance
            else:
                l1, l2 = bg_luminance, text_luminance

            # Calculate contrast ratio (avoid division by zero)
            contrast = (l1 + 0.05) / (l2 + 0.05)
            contrast = max(1.0, min(21.0, contrast))  # Clamp to [1.0, 21.0]

            # Store with class name key
            key = f'{class_name}_text_bg'
            contrast_ratios[key] = contrast
            class_index += 1

        return contrast_ratios

    except Exception:
        # Graceful error handling: return empty dict on any error
        return {}


def calculate_layout_symmetry(html_str: str) -> float:
    """Calculate layout balance using variance formula.

    Args:
        html_str: HTML string with flex layout

    Returns:
        Float 0.0 (asymmetric) to 1.0 (symmetric)

    Algorithm (Formula 2 - Variance-Based):
        1. Extract flex or height proportions from child divs
        2. Normalize to sum = 1.0
        3. Calculate variance
        4. Symmetry = 1 - min(variance, 1.0)

    Examples:
        - Three equal divs (flex: 1, 1, 1): variance = 0 → score = 1.0
        - Unequal (flex: 0.1, 0.8, 0.1): variance ≈ 0.11 → score ≈ 0.89
        - Single region: Return 1.0 (trivially symmetric)
        - No regions: Return 0.5 (neutral)
    """
    try:
        if not html_str or not html_str.strip():
            return 0.5

        soup = BeautifulSoup(html_str, 'html.parser')

        # Build a map of class names to flex/height values from CSS
        class_properties = {}
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            css_content = style_tag.string or ''
            # Extract all class definitions with flex or height
            class_defs = re.findall(r'\.([a-zA-Z0-9_-]+)\s*\{([^}]*)\}', css_content)
            for class_name, css_rules in class_defs:
                # Extract flex value
                flex_match = re.search(r'flex:\s*(\d+\.?\d*)', css_rules)
                if flex_match:
                    class_properties[class_name] = float(flex_match.group(1))
                # Extract height percentage
                else:
                    height_match = re.search(r'height:\s*(\d+\.?\d*)vh', css_rules)
                    if height_match:
                        class_properties[class_name] = float(height_match.group(1))

        # Find main container with flex children
        container = soup.find('div', class_='container')
        if not container:
            return 0.5

        # Extract proportions from child divs (from inline styles or CSS classes)
        proportions = []
        for child in container.find_all('div', recursive=False):
            style = child.get('style', '')
            class_names = child.get('class', [])
            if isinstance(class_names, str):
                class_names = [class_names]

            # Try to extract flex value from inline style
            flex_match = re.search(r'flex:\s*(\d+\.?\d*)', style)
            if flex_match:
                proportions.append(float(flex_match.group(1)))
                continue

            # Try to extract height percentage from inline style
            height_match = re.search(r'height:\s*(\d+\.?\d*)%', style)
            if height_match:
                proportions.append(float(height_match.group(1)) / 100.0)
                continue

            # Try to extract from CSS classes
            for class_name in class_names:
                if class_name in class_properties:
                    proportions.append(class_properties[class_name])
                    break

        if not proportions or len(proportions) == 1:
            return 1.0  # Single region or no regions: trivially symmetric

        # Normalize proportions
        total = sum(proportions)
        if total == 0:
            return 0.0  # Invalid data

        proportions = [p / total for p in proportions]

        # Calculate variance
        mean = sum(proportions) / len(proportions)
        variance = sum((p - mean) ** 2 for p in proportions) / len(proportions)

        # Map to symmetry score
        symmetry = 1.0 - min(variance, 1.0)
        return symmetry

    except Exception:
        # Graceful error handling: return neutral score on any error
        return 0.5


def calculate_accessibility_score(html_str: str) -> float:
    """Calculate WCAG 2.1 AA compliance score (0-100).

    Args:
        html_str: HTML string

    Returns:
        Float 0-100

    Scoring (Weighted):
        - Required elements (html, head, body, title): +10 each (max +40)
        - Semantic elements (h1, nav, main, footer): +5 each
        - Contrast ≥ 4.5 (AA): +2 per compliant pair, -1 per non-compliant
        - Image alt text: +5 each (max +20)
        - Form labels: +5 each (max +20)
        - Heading hierarchy: +10 (h1 present, no skipped levels)
        Final: clamp(score, 0, 100)

    Examples:
        - Well-formed, good contrast: 80-95
        - Minimal, low contrast: 20-40
        - Empty: 0-10
    """
    try:
        if not html_str or not html_str.strip():
            return 0.0

        soup = BeautifulSoup(html_str, 'html.parser')
        score = 0.0

        # 1. Required elements (+10 each, max +40)
        if soup.find('html'):
            score += 10
        if soup.find('head'):
            score += 10
        if soup.find('body'):
            score += 10
        if soup.find('title'):
            score += 10

        # 2. Semantic elements (+5 each)
        if soup.find('h1'):
            score += 5
        if soup.find('nav'):
            score += 5
        if soup.find('main'):
            score += 5
        if soup.find('footer'):
            score += 5

        # 3. Contrast analysis (+2/-1)
        contrast_ratios = extract_contrast_ratios(html_str)
        wcag_aa_threshold = 4.5
        if contrast_ratios:
            for ratio in contrast_ratios.values():
                if ratio >= wcag_aa_threshold:
                    score += 2
                else:
                    score -= 1

        # 4. Image alt text (+5 each, max +20)
        images = soup.find_all('img')
        alt_count = sum(1 for img in images if img.get('alt'))
        score += min(alt_count * 5, 20)

        # 5. Form labels (+5 each, max +20)
        labels = soup.find_all('label')
        label_count = len(labels)
        score += min(label_count * 5, 20)

        # 6. Heading hierarchy (+10)
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if headings and headings[0].name == 'h1':
            # Check for skipped levels
            h_levels = [int(h.name[1]) for h in headings]
            skipped = False
            for i in range(len(h_levels) - 1):
                if h_levels[i + 1] - h_levels[i] > 1:
                    skipped = True
                    break
            if not skipped:
                score += 10

        # Clamp to 0-100
        score = max(0.0, min(100.0, score))
        return score

    except Exception:
        # Graceful error handling: return 0 on any error
        return 0.0


def extract_responsive_breakpoints(html_str: str) -> list[int]:
    """Extract media query breakpoints from CSS.

    Args:
        html_str: HTML string with <style> tag

    Returns:
        Sorted list of integers, e.g., [480, 768, 1024]
        Empty list if no breakpoints found

    Pattern: Matches @media (min-width: Npx) and (max-width: Npx)
    """
    try:
        if not html_str or not html_str.strip():
            return []

        # Extract CSS from style tags
        style_tags = re.findall(r'<style[^>]*>(.*?)</style>', html_str, re.DOTALL | re.IGNORECASE)
        all_css = ' '.join(style_tags)

        # Find all media query breakpoints
        breakpoints = set()
        patterns = [
            r'@media[^{]*\(\s*(?:min-width|max-width)\s*:\s*(\d+)px',
            r'@media[^{]*\(\s*(?:min-width|max-width)\s*:\s*(\d+)em',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, all_css, re.IGNORECASE)
            for match in matches:
                try:
                    if pattern.endswith('em'):
                        # Convert em to px (assuming 16px base)
                        breakpoints.add(int(float(match) * 16))
                    else:
                        breakpoints.add(int(match))
                except (ValueError, TypeError):
                    continue

        return sorted(list(breakpoints))

    except Exception:
        # Graceful error handling: return empty list on any error
        return []
