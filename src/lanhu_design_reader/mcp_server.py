import argparse
import asyncio
import os
from pathlib import Path
from typing import Any

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: install with `pip install -e .[mcp]`") from exc

from .client import LanhuDesignClient


mcp = FastMCP("Lanhu Design Reader")


def _resolve_image_id(client: LanhuDesignClient, url: str, image_id: str | None) -> tuple[dict[str, str | None], str]:
    params = client.parse_url(url)
    resolved = image_id or params.get("doc_id")
    if not resolved:
        raise ValueError("Missing image_id. Pass image_id or include image_id/docId in the Lanhu URL.")
    return params, resolved


async def _with_client(coro):
    async with LanhuDesignClient() as client:
        return await coro(client)


@mcp.tool()
async def lanhu_get_designs(url: str) -> dict[str, Any]:
    """Get design image list from a Lanhu UI project URL."""

    async def run(client: LanhuDesignClient):
        return await client.get_designs(url)

    return await _with_client(run)


@mcp.tool()
async def lanhu_get_design_slices(url: str, image_id: str | None = None, include_metadata: bool = True) -> dict[str, Any]:
    """Get slice metadata and scale URLs for one Lanhu design image."""

    async def run(client: LanhuDesignClient):
        params, resolved_image_id = _resolve_image_id(client, url, image_id)
        return await client.get_design_slices_info(
            resolved_image_id,
            params["team_id"],
            params["project_id"],
            include_metadata=include_metadata,
        )

    return await _with_client(run)


@mcp.tool()
async def lanhu_download_slices(
    url: str,
    image_id: str | None = None,
    scale: str = "ios_2x",
    output_dir: str = "./lanhu_slices",
    include_metadata: bool = False,
) -> dict[str, Any]:
    """Download slices for one Lanhu design image using a scale key.

    Common scale values:
    - Web: 1x, 2x, 3x
    - iOS: ios_2x, ios_3x
    - Android: android_mdpi, android_hdpi, android_xhdpi, android_xxhdpi, android_xxxhdpi
    """

    async def run(client: LanhuDesignClient):
        params, resolved_image_id = _resolve_image_id(client, url, image_id)
        slices_info = await client.get_design_slices_info(
            resolved_image_id,
            params["team_id"],
            params["project_id"],
            include_metadata=include_metadata,
        )
        paths = await client.download_slice_urls(slices_info, output_dir, scale)
        return {
            "scale": scale,
            "output_dir": str(Path(output_dir).resolve()),
            "count": len(paths),
            "downloaded": [str(path) for path in paths],
        }

    return await _with_client(run)


@mcp.tool()
async def lanhu_get_sketch_json(url: str, image_id: str | None = None) -> dict[str, Any]:
    """Get raw Sketch/PS JSON for one Lanhu design image."""

    async def run(client: LanhuDesignClient):
        params, resolved_image_id = _resolve_image_id(client, url, image_id)
        return await client.get_sketch_json(resolved_image_id, params["team_id"], params["project_id"])

    return await _with_client(run)


@mcp.tool()
async def lanhu_get_schema_json(url: str, image_id: str | None = None) -> dict[str, Any]:
    """Get DDS schema JSON for one Lanhu design image."""

    async def run(client: LanhuDesignClient):
        params, resolved_image_id = _resolve_image_id(client, url, image_id)
        return await client.get_design_schema_json(resolved_image_id, params["team_id"], params["project_id"])

    return await _with_client(run)


def main() -> None:
    parser = argparse.ArgumentParser(prog="lh-design-mcp")
    parser.add_argument("--transport", choices=["stdio", "http"], default=os.getenv("MCP_TRANSPORT", "stdio"))
    parser.add_argument("--host", default=os.getenv("SERVER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SERVER_PORT", "8001")))
    parser.add_argument("--path", default=os.getenv("MCP_PATH", "/mcp"))
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", path=args.path, host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
