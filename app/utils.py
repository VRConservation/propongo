"""Utility functions for Propongo."""

import io
import json
import math
import logging
import urllib.request
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from .config import Config

logger = logging.getLogger(__name__)


def normalize_geolibre_project_url(url: str) -> str:
    """Return a fetchable .geolibre.json URL for a shared GeoLibre project.

    GeoLibre's Share dialog hands out extension-less page links
    (https://share.geolibre.app/user/project), but the embed's `url=` param
    needs the raw project file. Appends `.geolibre.json` when the host is
    share.geolibre.app and the extension is missing.
    """
    url = (url or "").strip()
    if not url:
        return url
    if "share.geolibre.app" in url and not url.rstrip("/").endswith(".geolibre.json"):
        url = url.rstrip("/") + ".geolibre.json"
    return url


def build_geolibre_embed_src(config: dict, layout: str = "viewer") -> str:
    """Build the GeoLibre iframe URL from a proposal's map_config.

    Args:
        config: The proposal's map_config dict (mode + optional url).
        layout: GeoLibre layout mode — ``"viewer"`` (interactive),
            ``"print"`` (clean map-only export), etc.

    Returns:
        A URL to the configured GeoLibre embed. Nested URLs are
        percent-encoded so their query strings are not parsed by GeoLibre.
    """
    config = config or {}
    params = {"layout": layout, "welcome": "0"}
    url = (config.get("url") or "").strip()
    if config.get("mode") == "data_url" and url:
        params["data"] = url
    elif config.get("mode") == "project_url" and url:
        params["url"] = normalize_geolibre_project_url(url)
    return f"{Config.GEOLIBRE_EMBED_URL}?{urlencode(params)}"


def build_export_context(proposal) -> Dict[str, Any]:
    """Build context dictionary for export and preview templates.
    
    Args:
        proposal: Proposal object
        
    Returns:
        dict: Context dictionary with all necessary template variables
    """
    indirect_percent = getattr(proposal, 'indirect_percent', 0) or 0
    indirect_amount = proposal.total_budget * (indirect_percent / 100)
    total_with_indirect = proposal.total_budget + indirect_amount

    tasks_with_timing = []
    for t in proposal.tasks:
        tasks_with_timing.append({
            "id": t.get("id", ""),
            "name": t.get("name", ""),
            "description": t.get("description", ""),
            "lead_entity": t.get("lead_entity", ""),
            "start_month": t.get("start_month"),
            "start_year": t.get("start_year"),
            "duration_months": t.get("duration_months", 1),
            "recurring": t.get("recurring", False),
            "recurring_interval": t.get("recurring_interval", 3),
        })

    budget_with_timing = []
    timings = proposal.budget_item_timings or {}
    for item in proposal.budget_items:
        item_id = item.get("id", "")
        timing = timings.get(item_id, {})
        budget_with_timing.append({
            **item,
            "start_month": timing.get("start_month"),
            "start_year": timing.get("start_year"),
            "duration_months": timing.get("duration_months", 1),
            "task_id": item.get("task_id", ""),
            "recurring": timing.get("recurring", False),
            "recurring_interval": timing.get("recurring_interval", 3),
        })

    from datetime import datetime as _dt
    try:
        sd = _dt.strptime(proposal.start_date, "%Y-%m-%d")
        proj_start_month = sd.month
        proj_start_year = sd.year
    except (ValueError, TypeError):
        proj_start_month = 1
        proj_start_year = 2025

    try:
        ed = _dt.strptime(proposal.end_date, "%Y-%m-%d") if proposal.end_date else None
        proj_end_month = ed.month if ed else proj_start_month
        proj_end_year = ed.year if ed else proj_start_year + 1
    except (ValueError, TypeError):
        proj_end_month = proj_start_month
        proj_end_year = proj_start_year + 1

    if proposal.end_date:
        timeline_total_months = max((proj_end_year - proj_start_year) * 12 + (proj_end_month - proj_start_month) + 1, 1)
    else:
        max_end = 0
        for t in tasks_with_timing:
            sm = t.get("start_month") or proj_start_month
            sy = t.get("start_year") or proj_start_year
            offset = (sy - proj_start_year) * 12 + (sm - proj_start_month)
            dur = t.get("duration_months") or 1
            if t.get("recurring"):
                interval = t.get("recurring_interval") or 3
                last = offset
                while last < 120:
                    end = last + dur
                    if end > max_end:
                        max_end = end
                    last += interval
            else:
                end = offset + dur
                if end > max_end:
                    max_end = end
        for bi in budget_with_timing:
            sm = bi.get("start_month") or proj_start_month
            sy = bi.get("start_year") or proj_start_year
            offset = (sy - proj_start_year) * 12 + (sm - proj_start_month)
            dur = bi.get("duration_months") or 1
            if bi.get("recurring"):
                interval = bi.get("recurring_interval") or 3
                last = offset
                while last < 120:
                    end = last + dur
                    if end > max_end:
                        max_end = end
                    last += interval
            else:
                end = offset + dur
                if end > max_end:
                    max_end = end
        timeline_total_months = max(max_end, 1)
    if timeline_total_months <= 12:
        timeline_granularity = "months"
    elif timeline_total_months <= 36:
        timeline_granularity = "quarters"
    else:
        timeline_granularity = "years"

    task_bi_data = {}
    for bi in budget_with_timing:
        tid = bi.get("task_id", "")
        if not tid:
            continue
        sm = bi.get("start_month") or proj_start_month
        sy = bi.get("start_year") or proj_start_year
        bi_offset = (sy - proj_start_year) * 12 + (sm - proj_start_month)
        bi_dur = bi.get("duration_months") or 1
        if tid not in task_bi_data:
            task_bi_data[tid] = {"min_offset": bi_offset, "max_end": bi_offset + bi_dur}
        else:
            task_bi_data[tid]["min_offset"] = min(task_bi_data[tid]["min_offset"], bi_offset)
            task_bi_data[tid]["max_end"] = max(task_bi_data[tid]["max_end"], bi_offset + bi_dur)

    all_rows = []
    for t in tasks_with_timing:
        sm = t.get("start_month") or proj_start_month
        sy = t.get("start_year") or proj_start_year
        offset = (sy - proj_start_year) * 12 + (sm - proj_start_month)
        dur = t.get("duration_months") or 1
        tid = t.get("id", "")
        recurring = t.get("recurring", False)
        interval = t.get("recurring_interval") or 3

        if tid in task_bi_data:
            offset = task_bi_data[tid]["min_offset"]
            dur = task_bi_data[tid]["max_end"] - task_bi_data[tid]["min_offset"]
            if dur < 1:
                dur = 1
            recurring = False

        if recurring:
            bars = []
            r_offset = offset
            while r_offset < timeline_total_months:
                bars.append({"offset": r_offset, "duration": dur})
                r_offset += interval
            all_rows.append({
                "name": t.get("name", ""),
                "bars": bars,
                "is_indent": False,
                "lead_entity": t.get("lead_entity", ""),
            })
        else:
            all_rows.append({
                "name": t.get("name", ""),
                "bars": [{"offset": offset, "duration": dur}],
                "is_indent": False,
                "lead_entity": t.get("lead_entity", ""),
            })

        for bi in budget_with_timing:
            if bi.get("task_id") == tid:
                bi_sm = bi.get("start_month") or sm
                bi_sy = bi.get("start_year") or sy
                bi_offset = (bi_sy - proj_start_year) * 12 + (bi_sm - proj_start_month)
                bi_dur = bi.get("duration_months") or 1
                bi_recurring = bi.get("recurring", False)
                bi_interval = bi.get("recurring_interval") or 3
                if bi_recurring:
                    bars = []
                    br_offset = bi_offset
                    while br_offset < timeline_total_months:
                        bars.append({"offset": br_offset, "duration": bi_dur})
                        br_offset += bi_interval
                    all_rows.append({
                        "name": bi.get("name", ""),
                        "bars": bars,
                        "is_indent": True,
                        "lead_entity": "",
                    })
                else:
                    all_rows.append({
                        "name": bi.get("name", ""),
                        "bars": [{"offset": bi_offset, "duration": bi_dur}],
                        "is_indent": True,
                        "lead_entity": "",
                    })

    return {
        "proposal": proposal,
        "tasks": tasks_with_timing,
        "budget_items": proposal.budget_items,
        "budget_with_timing": budget_with_timing,
        "total_budget": proposal.total_budget,
        "indirect_percent": indirect_percent,
        "indirect_amount": indirect_amount,
        "total_with_indirect": total_with_indirect,
        "timeline_granularity": timeline_granularity,
        "timeline_total_months": timeline_total_months,
        "all_rows": all_rows,
        "budget_by_year": build_budget_by_year(proposal),
        "map_ctx": build_map_export_context(proposal),
    }


def build_map_export_context(proposal) -> Dict[str, Any]:
    """Build the Map figure context for preview and export templates.

    Returns None unless the proposal opts in via map_config.show_in_preview.
    When a static image URL is configured it is preferred; otherwise the live
    GeoLibre embed URL is provided (renders in browsers and, once captured to
    a clean map image, in the Chromium PDF export). ``share_url`` is the
    human-facing GeoLibre project link used in the Markdown export.
    """
    map_config = getattr(proposal, "map_config", None) or {}
    if not map_config.get("show_in_preview"):
        return None
    url = (map_config.get("url") or "").strip()
    share_url = None
    if url and map_config.get("mode") in ("project_url", "data_url"):
        share_url = url.rstrip("/")
        if share_url.endswith(".geolibre.json"):
            share_url = share_url[: -len(".geolibre.json")]
    return {
        "embed_src": build_geolibre_embed_src(map_config),
        "image_url": (map_config.get("image_url") or "").strip(),
        "share_url": share_url,
        "caption": (map_config.get("caption") or "").strip().rstrip("."),
    }


def build_map_export_image(proposal):
    """Try to produce a raster PNG image of the map.

    Used by the on-screen print preview so a static image can be swapped in
    for printing. Returns a ``bytes`` PNG payload or *None*.  Checks, in
    order:
    1. A user-supplied ``image_url`` in map_config (fetched over HTTP).
    2. A Playwright screenshot of the GeoLibre embed (all modes).
    3. An auto-generated tile map from a GeoJSON ``data_url``.
    4. For project_url mode, fetches the .geolibre.json project file,
       looks for embedded data URLs, and generates a tile map from the first one.
    5. For basemap-only mode (no data URL), stitches a default basemap.
    """
    map_config = getattr(proposal, "map_config", None) or {}
    if not map_config.get("show_in_preview"):
        return None

    image_url = (map_config.get("image_url") or "").strip()
    if image_url:
        try:
            req = urllib.request.Request(
                image_url,
                headers={"User-Agent": "Propongo/1.0 (proposal-generator)"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except Exception as exc:
            logger.warning("Could not fetch map image_url %s: %s", image_url, exc)

    embed_src = build_geolibre_embed_src(map_config)
    screenshot = _screenshot_embed(embed_src)
    if screenshot:
        return screenshot

    url = (map_config.get("url") or "").strip()
    mode = map_config.get("mode", "")

    if url and mode == "data_url":
        return generate_static_map_image(url)

    if url and mode == "project_url":
        return _generate_map_from_project_tiles(
            normalize_geolibre_project_url(url)
        )

    return _generate_basemap_image()


def _generate_map_from_project(project_url):
    """Generate a map image for *project_url*.

    Tries Playwright first (renders all layers via the browser's native
    COG tiling).  Falls back to tile-stitching if Playwright is not
    available.
    """
    embed_src = build_geolibre_embed_src(
        {"mode": "project_url", "url": project_url},
    )
    screenshot = _screenshot_embed(embed_src)
    if screenshot:
        return screenshot

    return _generate_map_from_project_tiles(project_url)


def _screenshot_embed(embed_url, width=1200, height=800, timeout=30):
    """Open *embed_url* in a headless browser and screenshot just the map canvas.

    Uses 2× device pixel ratio so the captured image is crisp when
    printed.  Resizes the result to 800×450 for export figures.
    Returns PNG bytes or *None* if Playwright is not installed or fails.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=2,
            )
            page.goto(embed_url, timeout=timeout * 1000)
            try:
                page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            except Exception:
                pass
            page.wait_for_timeout(4000)

            canvas = page.locator("canvas")
            if canvas.count() > 0:
                buf = canvas.first.screenshot(type="png")
            else:
                buf = page.screenshot(type="png")

            browser.close()

            if buf:
                from PIL import Image
                import io
                im = Image.open(io.BytesIO(buf))
                # Canvas at 2x DPR is ~1600×900; resize to 800×450
                target = (800, 450)
                if im.size != target:
                    im = im.resize(target, Image.LANCZOS)
                    out = io.BytesIO()
                    im.save(out, format="PNG", optimize=True)
                    return out.getvalue()
                return buf
            return None
    except Exception as exc:
        logger.debug("Playwright screenshot failed: %s", exc)
        return None


def _generate_map_from_project_tiles(project_url):
    """Fetch a .geolibre.json project and render via tile stitching + overlays.

    Used as a fallback when Playwright is not available.
    """
    try:
        req = urllib.request.Request(
            project_url,
            headers={"User-Agent": "Propongo/1.0 (proposal-generator)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            project_data = json.loads(resp.read())
    except Exception as exc:
        logger.debug("Could not fetch geolibre project %s: %s", project_url, exc)
        return None

    bbox_raw = (project_data.get("mapView") or {}).get("bbox")
    if not bbox_raw or len(bbox_raw) != 4:
        return None
    bbox = (bbox_raw[0], bbox_raw[1], bbox_raw[2], bbox_raw[3])

    basemap = _stitch_basemap_tiles(bbox)
    if basemap is None:
        return None

    layers = project_data.get("layers") or []
    if not layers:
        return basemap

    try:
        from PIL import Image
        basemap_img = Image.open(io.BytesIO(basemap)).convert("RGBA")
    except Exception:
        return basemap

    for layer in layers:
        if not layer.get("visible", True):
            continue
        layer_type = layer.get("type", "")
        source = layer.get("source") or {}
        style = layer.get("style") or {}

        if layer_type == "cog":
            cog_url = source.get("url", "")
            if cog_url:
                overlay = _render_cog_layer(cog_url, bbox, basemap_img.size, style)
                if overlay is not None:
                    basemap_img = Image.alpha_composite(basemap_img, overlay)

        elif layer_type == "geojson":
            geojson_data = layer.get("geojson")
            geojson_url = source.get("url", "")
            if not geojson_data and geojson_url:
                try:
                    req2 = urllib.request.Request(
                        geojson_url,
                        headers={"User-Agent": "Propongo/1.0 (proposal-generator)"},
                    )
                    with urllib.request.urlopen(req2, timeout=15) as resp2:
                        geojson_data = json.loads(resp2.read())
                except Exception:
                    continue
            if geojson_data:
                overlay = _render_geojson_layer(geojson_data, bbox, basemap_img.size, style)
                if overlay is not None:
                    basemap_img = Image.alpha_composite(basemap_img, overlay)

    buf = io.BytesIO()
    basemap_img.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _render_cog_layer(cog_url, bbox, target_size, style=None):
    """Render a COG raster as a semi-transparent RGBA overlay.

    Picks the coarsest overview that still gives at least 2× the target
    resolution, so the output is sharp when downscaled.  Returns a PIL
    RGBA Image or *None* on failure.
    """
    try:
        import rasterio
        from rasterio.windows import from_bounds
        import numpy as np
        from PIL import Image
    except ImportError:
        logger.debug("rasterio not installed – cannot render COG layer")
        return None

    min_lon, min_lat, max_lon, max_lat = bbox
    width, height = target_size

    try:
        with rasterio.open(cog_url) as src:
            overviews = src.overviews(1)
            # Pick the coarsest overview that still gives ≥2× target width
            target_w = width * 2
            if overviews:
                decimation = overviews[-1]
                for ov in overviews:
                    if src.width // ov >= target_w:
                        decimation = ov
                        break
            else:
                decimation = 1

            out_h = max(src.height // decimation, 1)
            out_w = max(src.width // decimation, 1)
            window = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
            data = src.read(
                1,
                window=window,
                out_shape=(out_h, out_w),
                boundless=True,
                masked=True,
            )

            if data.size == 0 or data.mask.all():
                return None

            cmap = _get_raster_colormap(src)
            if not cmap:
                cmap = _NLCD_COLORMAP

            rows, cols = np.nonzero(~data.mask)
            if len(rows) == 0:
                return None

            rmin, rmax = rows.min(), rows.max()
            cmin, cmax = cols.min(), cols.max()
            data = data[rmin:rmax + 1, cmin:cmax + 1]
            h, w = data.shape

            rgba = np.zeros((h, w, 4), dtype=np.uint8)
            for val, (r, g, b, a) in cmap.items():
                mask = data == val
                rgba[mask, 0] = r
                rgba[mask, 1] = g
                rgba[mask, 2] = b
                rgba[mask, 3] = a

            no_colormap = (~data.mask) & ~np.isin(data, list(cmap.keys())) & (data != 0)
            rgba[no_colormap] = [100, 150, 255, 128]

            img = Image.fromarray(rgba, "RGBA")
            img = img.resize((width, height), Image.LANCZOS)
            return img

    except Exception as exc:
        logger.debug("Could not render COG %s: %s", cog_url, exc)
        return None


def _render_geojson_layer(geojson_data, bbox, target_size, style=None):
    """Render GeoJSON features as a semi-transparent RGBA overlay.

    *geojson_data* is a GeoJSON FeatureCollection or Feature dict.
    *bbox* is ``(min_lon, min_lat, max_lon, max_lat)``.
    *target_size* is ``(width, height)`` in pixels for the output.
    *style* is the layer style dict from the geolibre project.

    Returns a PIL RGBA Image or *None* on failure.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    min_lon, min_lat, max_lon, max_lat = bbox
    width, height = target_size

    bbox_width = max_lon - min_lon
    bbox_height = max_lat - min_lat
    if bbox_width <= 0 or bbox_height <= 0:
        return None

    style = style or {}
    fill_color = style.get("fillColor", "#3b82f6")
    stroke_color = style.get("strokeColor", "#e66100")
    stroke_width = max(int(style.get("strokeWidth", 3)), 1)
    fill_opacity = style.get("fillOpacity", 0.3)

    def _hex_to_rgba(hex_color, alpha=255):
        if not hex_color or not isinstance(hex_color, str):
            return (0, 0, 0, 0)
        h = hex_color.lstrip("#")
        if len(h) < 6 or not all(c in "0123456789abcdefABCDEF" for c in h[:6]):
            return (0, 0, 0, 0)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r, g, b, alpha)

    fill = _hex_to_rgba(fill_color, int(fill_opacity * 255))
    stroke = _hex_to_rgba(stroke_color, 220)

    features = []
    if geojson_data.get("type") == "FeatureCollection":
        features = geojson_data.get("features", [])
    elif geojson_data.get("type") == "Feature":
        features = [geojson_data]

    if not features:
        return None

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for feat in features:
        geom = feat.get("geometry", {})
        geom_type = geom.get("type", "")
        coords = geom.get("coordinates", [])

        def _project(lon, lat):
            x = (lon - min_lon) / bbox_width * width
            y = (1 - (lat - min_lat) / bbox_height) * height
            return (x, y)

        rings = []
        if geom_type == "Polygon":
            rings = coords
        elif geom_type == "MultiPolygon":
            rings = [ring for poly in coords for ring in poly]

        for ring in rings:
            projected = [_project(c[0], c[1]) for c in ring]
            if len(projected) < 3:
                continue
            draw.polygon(projected, fill=fill, outline=stroke, width=stroke_width)

    return img


def _get_raster_colormap(src):
    """Return a {value: (r, g, b, a)} colormap for the raster dataset.

    Uses the dataset's built-in colormap if present, otherwise falls back
    to a basic ramp for integer-coded rasters like NLCD.
    """
    try:
        cmap = src.colormap(1)
        if cmap:
            return {k: tuple(v) for k, v in cmap.items()}
    except Exception:
        pass

    return _NLCD_COLORMAP


_NLCD_COLORMAP = {
    0:  (0, 0, 0, 0),
    11: (65, 105, 225, 180),
    12: (135, 206, 235, 180),
    21: (255, 255, 190, 160),
    22: (255, 190, 190, 160),
    23: (255, 0, 0, 160),
    24: (180, 0, 0, 160),
    31: (255, 255, 0, 160),
    41: (0, 100, 0, 180),
    42: (0, 150, 0, 180),
    43: (0, 120, 80, 180),
    51: (100, 180, 100, 160),
    52: (60, 140, 60, 160),
    71: (150, 200, 150, 160),
    72: (100, 170, 100, 160),
    73: (80, 150, 80, 160),
    74: (60, 130, 60, 160),
    81: (200, 200, 100, 160),
    82: (170, 180, 90, 160),
    90: (0, 130, 150, 160),
    91: (100, 180, 210, 160),
    92: (0, 150, 180, 160),
    93: (0, 120, 160, 160),
    94: (0, 100, 140, 160),
    95: (0, 80, 120, 160),
}


def _bbox_from_geojson(data):
    """Extract a (min_lon, min_lat, max_lon, max_lat) bounding box from GeoJSON."""
    coords = []

    def _collect(geometry):
        t = geometry.get("type", "")
        c = geometry.get("coordinates")
        if c is None:
            return
        if t == "Point":
            coords.append(c)
        elif t in ("LineString", "MultiPoint"):
            coords.extend(c)
        elif t in ("Polygon", "MultiLineString"):
            for ring in c:
                coords.extend(ring)
        elif t == "MultiPolygon":
            for poly in c:
                for ring in poly:
                    coords.extend(ring)
        elif t == "GeometryCollection":
            for g in geometry.get("geometries", []):
                _collect(g)

    if data.get("type") == "FeatureCollection":
        for f in data.get("features", []):
            _collect(f.get("geometry", {}))
    elif data.get("type") == "Feature":
        _collect(data.get("geometry", {}))
    else:
        _collect(data)

    if not coords:
        return None
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return (min(lons), min(lats), max(lons), max(lats))


def _lon_lat_to_tile_xy(lon, lat, zoom):
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def _tile_xy_to_lon_lat(x, y, zoom):
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lon, lat


def generate_static_map_image(data_url, width=800, height=500):
    """Generate a static map PNG from a GeoJSON data URL.

    Downloads the GeoJSON, computes the bounding box, fetches OSM tiles,
    and stitches them into a single image.  Returns PNG bytes or *None*
    on failure (wrong format, network error, etc.).
    """
    try:
        req = urllib.request.Request(
            data_url,
            headers={"User-Agent": "Propongo/1.0 (proposal-generator)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        geojson = json.loads(raw)
    except Exception as exc:
        logger.debug("Could not fetch GeoJSON for static map: %s", exc)
        return None

    bbox = _bbox_from_geojson(geojson)
    if bbox is None:
        return None

    return _stitch_basemap_tiles(bbox, width, height)


def _generate_basemap_image(width=800, height=500):
    """Generate a static basemap image with no data layers.

    Used as a last-resort fallback for ``basemap`` mode (no URL) when a
    Playwright screenshot is not available.  Stitches OSM tiles for a
    default world-view bounding box.
    """
    default_bbox = (-170, -58, 170, 72)
    return _stitch_basemap_tiles(default_bbox, width, height)


def _stitch_basemap_tiles(bbox, width=800, height=500):
    """Fetch OSM tiles covering *bbox* and stitch them into a PNG image.

    *bbox* is ``(min_lon, min_lat, max_lon, max_lat)``.  Returns PNG
    bytes or *None* on failure.
    """
    try:
        from PIL import Image
    except ImportError:
        logger.debug("Pillow not installed – cannot generate static map")
        return None

    min_lon, min_lat, max_lon, max_lat = bbox

    zoom = 1
    for z in range(2, 16):
        x0, _ = _lon_lat_to_tile_xy(min_lon, max_lat, z)
        x1, _ = _lon_lat_to_tile_xy(max_lon, min_lat, z)
        if x1 - x0 >= 5:
            zoom = z - 1
            break
    else:
        zoom = 14

    tile_size = 256
    nx0, ny0 = _lon_lat_to_tile_xy(min_lon, max_lat, zoom)
    nx1, ny1 = _lon_lat_to_tile_xy(max_lon, min_lat, zoom)
    tw = nx1 - nx0 + 1
    th = ny1 - ny0 + 1

    canvas = Image.new("RGB", (tw * tile_size, th * tile_size))
    for tx in range(nx0, nx0 + tw):
        for ty in range(ny0, ny0 + th):
            try:
                url = f"https://tile.openstreetmap.org/{zoom}/{tx}/{ty}.png"
                treq = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Propongo/1.0 (proposal-generator)"},
                )
                with urllib.request.urlopen(treq, timeout=10) as resp:
                    tile = Image.open(io.BytesIO(resp.read()))
                canvas.paste(tile, ((tx - nx0) * tile_size, (ty - ny0) * tile_size))
            except Exception:
                continue

    fx0 = (_lon_lat_to_tile_xy(min_lon, max_lat, zoom)[0] - nx0) * tile_size
    fy0 = (_lon_lat_to_tile_xy(min_lon, max_lat, zoom)[1] - ny0) * tile_size
    fx1 = (_lon_lat_to_tile_xy(max_lon, min_lat, zoom)[0] - nx0 + 1) * tile_size
    fy1 = (_lon_lat_to_tile_xy(max_lon, min_lat, zoom)[1] - ny0 + 1) * tile_size
    canvas = canvas.crop((
        max(0, int(fx0)),
        max(0, int(fy0)),
        min(canvas.width, int(fx1)),
        min(canvas.height, int(fy1)),
    ))

    if canvas.width < 1 or canvas.height < 1:
        return None
    canvas = canvas.resize((width, height), Image.LANCZOS)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def build_budget_by_year(proposal) -> Dict[str, Any]:
    """Allocate budget items across calendar years based on their spend dates.

    Each item's cost is spread evenly over the months of its user-defined
    spend window (``budget_item_timings``). Items with no dates set are
    reported as unscheduled so totals still reconcile.
    """
    timings = getattr(proposal, "budget_item_timings", None) or {}
    by_year = {}
    unscheduled = []

    for item in proposal.budget_items:
        total = float(item.get("cost_per_unit", 0) * item.get("units", 0))
        if total <= 0:
            continue
        timing = timings.get(item.get("id", ""), {})
        sm = timing.get("start_month")
        sy = timing.get("start_year")
        dur = timing.get("duration_months")
        if not (sm and sy and dur):
            unscheduled.append({"name": item.get("name", ""), "amount": total})
            continue

        start = int(sy) * 12 + (int(sm) - 1)
        dur = max(int(dur), 1)
        monthly = total / dur
        for m in range(dur):
            y = (start + m) // 12
            by_year[y] = by_year.get(y, 0.0) + monthly

    years = [{"year": y, "amount": round(by_year[y], 2)} for y in sorted(by_year)]
    return {
        "years": years,
        "unscheduled": unscheduled,
        "total_scheduled": round(sum(r["amount"] for r in years), 2),
        "total_unscheduled": round(sum(u["amount"] for u in unscheduled), 2),
    }


def build_tracker_export_context(proposal) -> Dict[str, Any]:
    """Build context dictionary for tracker export templates.

    Args:
        proposal: Proposal object

    Returns:
        dict: Context dictionary with all necessary template variables
    """
    indirect_percent = getattr(proposal, 'indirect_percent', 0) or 0
    indirect_amount = proposal.total_budget * (indirect_percent / 100)
    total_with_indirect = proposal.total_budget + indirect_amount

    timings = proposal.budget_item_timings or {}
    task_budgets = {}
    for task in proposal.tasks:
        items = [b for b in proposal.budget_items if b.get("task_id") == task["id"]]
        for item in items:
            t = timings.get(item.get("id", ""), {})
            if t:
                item["actual_cost"] = t.get("actual_cost", 0)
        subtotal = sum(i.get("cost_per_unit", 0) * i.get("units", 0) for i in items)
        actual_total = sum(i.get("actual_cost", 0) for i in items)
        task_budgets[task["id"]] = {
            "task": task,
            "items": items,
            "subtotal": subtotal,
            "actual_total": actual_total,
        }

    total_actual = sum(tb["actual_total"] for tb in task_budgets.values())

    milestones = getattr(proposal, 'milestones', []) or []
    reports = getattr(proposal, 'reports', []) or []

    completed_tasks = sum(1 for t in proposal.tasks if t.get("status") == "completed")
    total_tasks = len(proposal.tasks)
    overall_pct = round(completed_tasks / total_tasks * 100) if total_tasks else 0

    return {
        "proposal": proposal,
        "tasks": proposal.tasks,
        "task_budgets": task_budgets,
        "total_budget": proposal.total_budget,
        "indirect_percent": indirect_percent,
        "indirect_amount": indirect_amount,
        "total_with_indirect": total_with_indirect,
        "total_actual": total_actual,
        "milestones": milestones,
        "reports": reports,
        "overall_pct": overall_pct,
    }
