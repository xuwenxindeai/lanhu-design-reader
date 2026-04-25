import asyncio
import sys

from lanhu_design_reader import LanhuDesignClient


async def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python examples/read_slices.py <lanhu_url> <image_id>")

    url = sys.argv[1]
    image_id = sys.argv[2]

    async with LanhuDesignClient() as client:
        params = client.parse_url(url)
        slices = await client.get_design_slices_info(image_id, params["team_id"], params["project_id"])
        print(f"total_slices={slices['total_slices']}")
        for item in slices["slices"]:
            print(item["id"], item["name"], item.get("size"), item.get("base_size") or item.get("logical_size"))


if __name__ == "__main__":
    asyncio.run(main())
