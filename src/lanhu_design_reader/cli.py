import argparse
import asyncio
import json
import sys
from pathlib import Path

from .client import LanhuDesignClient


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def _run(args) -> None:
    async with LanhuDesignClient(cookie=args.cookie, dds_cookie=args.dds_cookie) as client:
        params = client.parse_url(args.url)

        if args.command == "designs":
            _print_json(await client.get_designs(args.url))
            return

        image_id = args.image_id or params.get("doc_id")
        if not image_id:
            raise SystemExit("Missing image id. Pass --image-id or include image_id/docId in URL.")

        if args.command == "sketch":
            data = await client.get_sketch_json(image_id, params["team_id"], params["project_id"])
        elif args.command == "schema":
            data = await client.get_design_schema_json(image_id, params["team_id"], params["project_id"])
        elif args.command in ("slices", "download-slices"):
            data = await client.get_design_slices_info(
                image_id,
                params["team_id"],
                params["project_id"],
                include_metadata=not args.no_metadata,
            )
            if args.command == "download-slices":
                paths = await client.download_slice_urls(data, args.output, args.scale)
                _print_json({"downloaded": [str(path) for path in paths], "count": len(paths)})
                return
        else:
            raise SystemExit(f"Unknown command: {args.command}")

        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            client.dump_json(data, output)
            print(f"Wrote {output}")
        else:
            _print_json(data)


def main() -> None:
    parser = argparse.ArgumentParser(prog=Path(sys.argv[0]).name)
    parser.add_argument("--cookie", help="Lanhu cookie. Defaults to LANHU_COOKIE env.")
    parser.add_argument("--dds-cookie", help="DDS cookie. Defaults to DDS_COOKIE or LANHU_COOKIE env.")

    sub = parser.add_subparsers(dest="command", required=True)

    designs = sub.add_parser("designs", help="List design images in a Lanhu project")
    designs.add_argument("url")

    for name in ("sketch", "schema", "slices"):
        cmd = sub.add_parser(name, help=f"Read {name} data for one design")
        cmd.add_argument("url")
        cmd.add_argument("--image-id", help="Design image id; optional if URL has image_id/docId")
        cmd.add_argument("-o", "--output", help="Write JSON to file instead of stdout")
        if name == "slices":
            cmd.add_argument("--no-metadata", action="store_true", help="Omit slice metadata")

    download = sub.add_parser("download-slices", help="Download slice PNGs for one design")
    download.add_argument("url")
    download.add_argument("--image-id", help="Design image id; optional if URL has image_id/docId")
    download.add_argument("-o", "--output", required=True, help="Output directory")
    download.add_argument("--scale", default="ios_2x", help="Scale key, e.g. ios_2x, ios_3x, android_xhdpi")
    download.add_argument("--no-metadata", action="store_true", help="Omit slice metadata")

    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
