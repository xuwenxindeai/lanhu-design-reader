import json
import math
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _load_env_files() -> None:
    """Load local and user-level env files without overriding shell variables."""
    if load_dotenv is None:
        return

    repo_root = Path(__file__).resolve().parents[2]
    candidates = [
        os.getenv("LANHU_DESIGN_READER_ENV"),
        Path.cwd() / ".env",
        Path.home() / ".lanhu-design-reader" / ".env",
        repo_root / ".env",
    ]

    seen: set[Path] = set()
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path in seen or not path.exists():
            continue
        load_dotenv(path, override=False)
        seen.add(path)


_load_env_files()


BASE_URL = "https://lanhuapp.com"
DDS_BASE_URL = "https://dds.lanhuapp.com"


class LanhuDesignClient:
    """Small Lanhu design reader extracted from lanhu-mcp.

    It intentionally omits MCP, Playwright, Axure, and collaboration features.
    """

    def __init__(self, cookie: str | None = None, dds_cookie: str | None = None, timeout: float = 30):
        self.cookie = cookie or os.getenv("LANHU_COOKIE", "")
        self.dds_cookie = dds_cookie or os.getenv("DDS_COOKIE") or self.cookie
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://lanhuapp.com/web/",
            "Accept": "application/json, text/plain, */*",
            "Cookie": self.cookie,
            "request-from": "web",
            "real-path": "/item/project/stage",
        }
        self.client = httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self) -> None:
        await self.client.aclose()

    @staticmethod
    def parse_url(url: str) -> dict[str, str | None]:
        """Parse Lanhu project/stage URL or raw query string."""
        if url.startswith("http"):
            parsed = urlparse(url)
            fragment = parsed.fragment
            if not fragment:
                raise ValueError("Invalid Lanhu URL: missing fragment part")
            url = fragment.split("?", 1)[1] if "?" in fragment else fragment

        if url.startswith("?"):
            url = url[1:]

        params: dict[str, str] = {}
        for part in url.split("&"):
            if "=" in part:
                key, value = part.split("=", 1)
                params[key] = value

        team_id = params.get("tid")
        project_id = params.get("pid")
        doc_id = params.get("docId") or params.get("image_id")
        version_id = params.get("versionId")

        if not project_id:
            raise ValueError("URL parsing failed: missing required param pid")
        if not team_id:
            raise ValueError("URL parsing failed: missing required param tid")

        return {
            "team_id": team_id,
            "project_id": project_id,
            "doc_id": doc_id,
            "version_id": version_id,
        }

    async def get_designs(self, url: str) -> dict[str, Any]:
        """Return design image list for a Lanhu UI project."""
        params = self.parse_url(url)
        response = await self.client.get(
            f"{BASE_URL}/api/project/images",
            params={
                "project_id": params["project_id"],
                "team_id": params["team_id"],
                "dds_status": 1,
                "position": 1,
                "show_cb_src": 1,
                "comment": 1,
            },
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != "00000":
            raise RuntimeError(f"Failed to get designs: {data.get('msg', 'unknown error')}")

        project_data = data.get("data") or {}
        designs = []
        for idx, img in enumerate(project_data.get("images") or [], 1):
            designs.append(
                {
                    "index": idx,
                    "id": img.get("id"),
                    "name": img.get("name"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "url": img.get("url"),
                    "has_comment": img.get("has_comment", False),
                    "update_time": img.get("update_time"),
                }
            )

        return {
            "status": "success",
            "project_name": project_data.get("name"),
            "total_designs": len(designs),
            "designs": designs,
        }

    async def get_design_detail(self, image_id: str, team_id: str, project_id: str) -> dict[str, Any]:
        response = await self.client.get(
            f"{BASE_URL}/api/project/image",
            params={
                "dds_status": 1,
                "image_id": image_id,
                "team_id": team_id,
                "project_id": project_id,
            },
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != "00000":
            raise RuntimeError(f"Failed to get design: {data.get('msg', 'unknown error')}")
        return data.get("result") or {}

    async def get_sketch_json(self, image_id: str, team_id: str, project_id: str) -> dict[str, Any]:
        detail = await self.get_design_detail(image_id, team_id, project_id)
        versions = detail.get("versions") or []
        if not versions or not versions[0].get("json_url"):
            raise RuntimeError("Design has no json_url")
        response = await self.client.get(versions[0]["json_url"])
        response.raise_for_status()
        return response.json()

    async def get_design_schema_json(self, image_id: str, team_id: str, project_id: str) -> dict[str, Any]:
        """Fetch DDS schema JSON used by Lanhu's design renderer."""
        version_id = await self._get_version_id_by_image_id(project_id, team_id, image_id)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://dds.lanhuapp.com/",
            "Cookie": self.dds_cookie,
            "Authorization": "Basic dW5kZWZpbmVkOg==",
        }
        async with httpx.AsyncClient(timeout=self.client.timeout, headers=headers, follow_redirects=True) as dds_client:
            response = await dds_client.get(
                f"{DDS_BASE_URL}/api/dds/image/store_schema_revise",
                params={"version_id": version_id},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("code") != "00000":
                raise RuntimeError(f"DDS schema request failed: {data.get('msg', 'unknown error')}")
            schema_url = (data.get("data") or {}).get("data_resource_url")
            if not schema_url:
                raise RuntimeError("DDS schema response has no data_resource_url")
            schema_response = await dds_client.get(schema_url)
            schema_response.raise_for_status()
            return schema_response.json()

    async def get_design_slices_info(
        self,
        image_id: str,
        team_id: str,
        project_id: str,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """Extract slice metadata and scale URLs from Figma/Sketch/PS design JSON."""
        detail = await self.get_design_detail(image_id, team_id, project_id)
        versions = detail.get("versions") or []
        if not versions or not versions[0].get("json_url"):
            raise RuntimeError("Design has no json_url")

        json_response = await self.client.get(versions[0]["json_url"])
        json_response.raise_for_status()
        sketch_data = json_response.json()

        meta = sketch_data.get("meta") or {}
        slice_scale = int(sketch_data.get("sliceScale") or sketch_data.get("exportScale") or meta.get("sliceScale") or 2)
        is_figma = (meta.get("host") or {}).get("name") == "figma"
        slices: list[dict[str, Any]] = []

        def add_metadata(slice_info: dict[str, Any], obj: dict[str, Any]) -> None:
            if not include_metadata:
                return
            metadata: dict[str, Any] = {}
            if obj.get("fills"):
                metadata["fills"] = obj["fills"]
            if obj.get("borders") or obj.get("strokes"):
                metadata["borders"] = obj.get("borders") or obj.get("strokes")
            if "opacity" in obj:
                metadata["opacity"] = obj["opacity"]
            if obj.get("rotation"):
                metadata["rotation"] = obj["rotation"]
            if obj.get("textStyle"):
                metadata["text_style"] = obj["textStyle"]
            if obj.get("shadows"):
                metadata["shadows"] = obj["shadows"]
            if obj.get("radius") or obj.get("cornerRadius"):
                metadata["border_radius"] = obj.get("radius") or obj.get("cornerRadius")
            if metadata:
                slice_info["metadata"] = metadata

        def find_slices(obj: dict[str, Any], parent_name: str = "", layer_path: str = "") -> None:
            if not isinstance(obj, dict):
                return

            current_name = obj.get("name", "")
            current_path = f"{layer_path}/{current_name}" if layer_path else current_name

            image_data = obj.get("image")
            if image_data and (image_data.get("imageUrl") or image_data.get("svgUrl")):
                if not (is_figma and not obj.get("hasExportImage")):
                    download_url = image_data.get("imageUrl") or image_data.get("svgUrl")
                    logical_w, logical_h = self._read_layer_size(image_data.get("size"), obj)
                    slice_info = self._make_slice_info(
                        obj=obj,
                        name=current_name,
                        download_url=download_url,
                        logical_w=logical_w,
                        logical_h=logical_h,
                        fmt="png" if image_data.get("imageUrl") else "svg",
                        layer_path=current_path,
                        parent_name=parent_name,
                    )
                    if image_data.get("svgUrl") and image_data.get("imageUrl"):
                        slice_info["svg_url"] = image_data["svgUrl"]
                    if image_data.get("imageUrl"):
                        slice_info["scale_urls"] = self._build_scale_urls(download_url, logical_w, logical_h, slice_scale)
                    add_metadata(slice_info, obj)
                    slices.append(slice_info)

            elif obj.get("ddsImage") and obj["ddsImage"].get("imageUrl") and not is_figma:
                dds = obj["ddsImage"]
                logical_w, logical_h = self._read_layer_size(dds.get("size"), obj)
                slice_info = self._make_slice_info(
                    obj=obj,
                    name=current_name,
                    download_url=dds["imageUrl"],
                    logical_w=logical_w,
                    logical_h=logical_h,
                    fmt="png",
                    layer_path=current_path,
                    parent_name=parent_name,
                )
                slice_info["scale_urls"] = self._build_scale_urls(dds["imageUrl"], logical_w, logical_h, slice_scale)
                add_metadata(slice_info, obj)
                slices.append(slice_info)

            for child_key in ("layers", "children"):
                for child in obj.get(child_key) or []:
                    if isinstance(child, dict):
                        find_slices(child, current_name, current_path)

        if sketch_data.get("artboard") and sketch_data["artboard"].get("layers"):
            for layer in sketch_data["artboard"]["layers"]:
                find_slices(layer)
        elif sketch_data.get("info"):
            for item in sketch_data["info"]:
                find_slices(item)

        if str(sketch_data.get("type") or "").lower() == "ps":
            self._append_ps_slices(sketch_data, slices, include_metadata)

        return {
            "design_id": image_id,
            "design_name": detail.get("name"),
            "version": versions[0].get("version_info"),
            "slice_scale": slice_scale,
            "canvas_size": {
                "width": detail.get("width"),
                "height": detail.get("height"),
            },
            "total_slices": len(slices),
            "slices": slices,
        }

    async def download_slice_urls(self, slices_info: dict[str, Any], output_dir: str | Path, scale_key: str = "ios_2x") -> list[Path]:
        """Download slices using a selected scale key such as ios_2x, ios_3x, android_xhdpi."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        downloaded: list[Path] = []
        for item in slices_info.get("slices") or []:
            scale_urls = item.get("scale_urls") or {}
            url = scale_urls.get(scale_key) or item.get("download_url")
            if not url:
                continue
            safe_name = self._safe_filename(f"{item.get('id')}_{item.get('name') or 'slice'}.png")
            path = output / safe_name
            response = await self.client.get(url, headers={"Referer": "https://lanhuapp.com/"})
            response.raise_for_status()
            path.write_bytes(response.content)
            downloaded.append(path)
        return downloaded

    async def _get_version_id_by_image_id(self, project_id: str, team_id: str, image_id: str) -> str:
        response = await self.client.get(
            f"{BASE_URL}/api/project/multi_info",
            params={"project_id": project_id, "team_id": team_id, "img_limit": 500, "detach": 1},
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != "00000":
            raise RuntimeError(f"multi_info failed: {data.get('msg', 'unknown error')}")
        for img in (data.get("result") or {}).get("images") or []:
            if img.get("id") == image_id:
                version_id = img.get("latest_version")
                if version_id:
                    return version_id
                raise RuntimeError("Design has no latest_version")
        raise RuntimeError(f"image_id not found: {image_id}")

    @staticmethod
    def _read_layer_size(size: Any, obj: dict[str, Any]) -> tuple[float, float]:
        logical_w = logical_h = 0.0
        if isinstance(size, dict):
            logical_w = float(size.get("width") or 0)
            logical_h = float(size.get("height") or 0)
        if not logical_w or not logical_h:
            frame = obj.get("frame") or obj.get("bounds") or {}
            logical_w = float(frame.get("width") or 0)
            logical_h = float(frame.get("height") or 0)
            if not logical_w and "left" in frame and "right" in frame:
                logical_w = float(frame.get("right", 0)) - float(frame.get("left", 0))
                logical_h = float(frame.get("bottom", 0)) - float(frame.get("top", 0))
        return max(1.0, logical_w), max(1.0, logical_h)

    @staticmethod
    def _make_slice_info(
        obj: dict[str, Any],
        name: str,
        download_url: str,
        logical_w: float,
        logical_h: float,
        fmt: str,
        layer_path: str,
        parent_name: str = "",
    ) -> dict[str, Any]:
        frame = obj.get("frame") or obj.get("bounds") or {}
        x = frame.get("x", frame.get("left", obj.get("left", 0)))
        y = frame.get("y", frame.get("top", obj.get("top", 0)))
        info = {
            "id": obj.get("id"),
            "name": name,
            "type": obj.get("type") or obj.get("layerType") or obj.get("ddsType") or "bitmap",
            "download_url": download_url,
            "size": f"{int(round(logical_w))}x{int(round(logical_h))}",
            "format": fmt,
            "position": {"x": int(round(float(x or 0))), "y": int(round(float(y or 0)))},
            "layer_path": layer_path,
            "logical_size": {
                "width": int(round(logical_w)),
                "height": int(round(logical_h)),
                "note": "1x logical px",
            },
        }
        if parent_name:
            info["parent_name"] = parent_name
        return info

    def _append_ps_slices(self, sketch_data: dict[str, Any], slices: list[dict[str, Any]], include_metadata: bool) -> None:
        by_id: dict[Any, dict[str, Any]] = {}

        def index_layer(obj: dict[str, Any]) -> None:
            if not isinstance(obj, dict):
                return
            oid = obj.get("id")
            if oid is not None:
                by_id[oid] = obj
            for key in ("layers", "children"):
                for child in obj.get(key) or []:
                    if isinstance(child, dict):
                        index_layer(child)

        if isinstance(sketch_data.get("board"), dict):
            index_layer(sketch_data["board"])
        for section in sketch_data.get("info") or []:
            if isinstance(section, dict):
                index_layer(section)

        existing_ids = {item.get("id") for item in slices}
        for asset in sketch_data.get("assets") or []:
            if not isinstance(asset, dict) or not asset.get("isSlice"):
                continue
            layer_id = asset.get("id")
            if layer_id is None or layer_id in existing_ids:
                continue
            layer = by_id.get(layer_id)
            if not isinstance(layer, dict):
                continue
            images = layer.get("images") or {}
            download_url = images.get("png_xxxhd") or images.get("svg")
            if not download_url:
                continue

            base_w = float(layer.get("width") or 0)
            base_h = float(layer.get("height") or 0)
            if base_w <= 0 or base_h <= 0:
                bounds = asset.get("bounds") or {}
                base_w = float(bounds.get("right", 0)) - float(bounds.get("left", 0))
                base_h = float(bounds.get("bottom", 0)) - float(bounds.get("top", 0))
            base_w = max(1.0, base_w)
            base_h = max(1.0, base_h)
            logical_w = max(1.0, base_w / 2)
            logical_h = max(1.0, base_h / 2)

            name = asset.get("name") or layer.get("name") or "slice"
            slice_info = {
                "id": layer_id,
                "name": name,
                "type": layer.get("type") or "ps-slice",
                "download_url": download_url,
                "size": f"{int(round(base_w))}x{int(round(base_h))}",
                "format": "png" if images.get("png_xxxhd") else "svg",
                "position": {
                    "x": int(round(float(layer.get("left", 0)))),
                    "y": int(round(float(layer.get("top", 0)))),
                },
                "layer_path": name,
                "logical_size": {
                    "width": int(round(logical_w)),
                    "height": int(round(logical_h)),
                    "note": "1x logical px; PS slice base px equals iOS @2x / Android xhdpi",
                },
                "base_size": {
                    "width": int(round(base_w)),
                    "height": int(round(base_h)),
                    "note": "PS slice base px; equals iOS @2x / Android xhdpi",
                },
            }
            if images.get("png_xxxhd") and images.get("svg"):
                slice_info["svg_url"] = images["svg"]
            if images.get("png_xxxhd"):
                slice_info["scale_urls"] = self._build_ps_scale_urls(download_url, base_w, base_h)
            if include_metadata:
                metadata = {"source": "photoshop", "asset_id": layer_id}
                if asset.get("scaleType") is not None:
                    metadata["scaleType"] = asset["scaleType"]
                slice_info["metadata"] = metadata
            slices.append(slice_info)
            existing_ids.add(layer_id)

    @staticmethod
    def _build_scale_urls(image_url: str, logical_w: float, logical_h: float, slice_scale: int) -> dict[str, str]:
        if not image_url or not logical_w or not logical_h:
            return {}
        lw = max(1, int(round(logical_w)))
        lh = max(1, int(round(logical_h)))
        stored_w = lw * max(1, int(slice_scale))
        stored_h = lh * max(1, int(slice_scale))

        def make_url(w: int, h: int) -> str:
            w, h = max(1, w), max(1, h)
            if w == stored_w and h == stored_h:
                return image_url
            return f"{image_url}?x-oss-process=image/resize,w_{w},h_{h}/format,png"

        def js_round(v: float) -> int:
            return math.floor(v + 0.5)

        ios_base_w = stored_w / 4
        ios_base_h = stored_h / 4
        return {
            "1x": make_url(lw, lh),
            "2x": make_url(lw * 2, lh * 2),
            "3x": make_url(lw * 3, lh * 3),
            "ios_1x": make_url(js_round(ios_base_w), js_round(ios_base_h)),
            "ios_2x": make_url(js_round(ios_base_w * 2), js_round(ios_base_h * 2)),
            "ios_3x": make_url(js_round(ios_base_w * 3), js_round(ios_base_h * 3)),
            "android_mdpi": make_url(js_round(ios_base_w), js_round(ios_base_h)),
            "android_hdpi": make_url(js_round(ios_base_w * 1.5), js_round(ios_base_h * 1.5)),
            "android_xhdpi": make_url(js_round(ios_base_w * 2), js_round(ios_base_h * 2)),
            "android_xxhdpi": make_url(js_round(ios_base_w * 3), js_round(ios_base_h * 3)),
            "android_xxxhdpi": make_url(stored_w, stored_h),
        }

    @staticmethod
    def _build_ps_scale_urls(image_url: str, base_w: float, base_h: float) -> dict[str, str]:
        if not image_url or not base_w or not base_h:
            return {}
        bw = max(1, int(round(base_w)))
        bh = max(1, int(round(base_h)))

        def js_round(v: float) -> int:
            return math.floor(v + 0.5)

        def make_url(w: int, h: int) -> str:
            w, h = max(1, w), max(1, h)
            return f"{image_url}?x-oss-process=image/resize,w_{w},h_{h}/format,png"

        one_x_w = bw / 2
        one_x_h = bh / 2
        return {
            "1x": make_url(js_round(one_x_w), js_round(one_x_h)),
            "2x": make_url(bw, bh),
            "3x": make_url(js_round(one_x_w * 3), js_round(one_x_h * 3)),
            "ios_1x": make_url(js_round(one_x_w), js_round(one_x_h)),
            "ios_2x": make_url(bw, bh),
            "ios_3x": make_url(js_round(one_x_w * 3), js_round(one_x_h * 3)),
            "android_mdpi": make_url(js_round(one_x_w), js_round(one_x_h)),
            "android_hdpi": make_url(js_round(one_x_w * 1.5), js_round(one_x_h * 1.5)),
            "android_xhdpi": make_url(bw, bh),
            "android_xxhdpi": make_url(js_round(one_x_w * 3), js_round(one_x_h * 3)),
            "android_xxxhdpi": make_url(js_round(one_x_w * 4), js_round(one_x_h * 4)),
        }

    @staticmethod
    def _safe_filename(name: str) -> str:
        return "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in name).strip()

    @staticmethod
    def dump_json(data: Any, path: str | Path) -> None:
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
