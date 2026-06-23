import argparse
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional

from quark_client import QuarkClient
from quark_client.config import Config


TreeNode = Dict[str, Any]
DEFAULT_OUTPUT_FILE = os.path.join("download", "tree.txt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Get a Quark Drive folder tree with quarkpan/quark_client."
    )
    parser.add_argument(
        "target",
        help=(
            "Share URL, Quark folder id, or path in your own drive. "
            "Use 0 for drive root."
        ),
    )
    parser.add_argument(
        "--source",
        choices=("auto", "share", "drive"),
        default="auto",
        help="Input type. Default: auto.",
    )
    parser.add_argument(
        "--pdir-fid",
        default="0",
        help="Folder id inside a share URL. Default: 0.",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Share extraction code/password. If omitted, try to parse from URL text.",
    )
    parser.add_argument(
        "--cookie",
        default=os.getenv("QUARK_COOKIE"),
        help="Quark cookie. Defaults to env QUARK_COOKIE.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Page size for each API request. Default: 100.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Limit recursion depth. Root children are depth 1. Default: unlimited.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of a text tree.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILE,
        help=f"Save output to this file. Default: {DEFAULT_OUTPUT_FILE}.",
    )
    return parser.parse_args()


def is_share_target(target: str) -> bool:
    return "pan.quark.cn/s/" in target or target.startswith("quark://share/")


def extract_share_url_and_password(text: str) -> tuple[str, Optional[str]]:
    password_patterns = [
        r"(?:提取码|密码|code)[:：]?\s*([A-Za-z0-9]+)",
        r"pwd=([A-Za-z0-9]+)",
    ]
    password = None
    for pattern in password_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            password = match.group(1)
            break

    url_match = re.search(r"https://pan\.quark\.cn/s/[A-Za-z0-9]+", text)
    if url_match:
        return url_match.group(0), password

    share_match = re.search(r"quark://share/[A-Za-z0-9]+", text)
    if share_match:
        return share_match.group(0), password

    return text, password


def response_items(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = response.get("data", response)
    if isinstance(data, dict):
        for key in ("list", "items", "files"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    if isinstance(data, list):
        return data
    return []


def response_total(response: Dict[str, Any]) -> Optional[int]:
    data = response.get("data", response)
    if isinstance(data, dict):
        for key in ("total", "_total", "count"):
            value = data.get(key)
            if isinstance(value, int):
                return value
    return None


def item_name(item: Dict[str, Any]) -> str:
    return str(item.get("file_name") or item.get("name") or item.get("title") or "")


def item_fid(item: Dict[str, Any]) -> str:
    return str(item.get("fid") or item.get("file_id") or item.get("id") or "")


def item_size(item: Dict[str, Any]) -> int:
    value = item.get("size") or item.get("file_size") or 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def item_is_folder(item: Dict[str, Any]) -> bool:
    if "dir" in item:
        return bool(item["dir"])
    if "is_dir" in item:
        return bool(item["is_dir"])
    if "file_type" in item:
        return item.get("file_type") == 0
    if "type" in item:
        return str(item["type"]).lower() in {"folder", "dir", "0"}
    return item_size(item) == 0 and not item.get("format_type")


def make_node(item: Dict[str, Any]) -> TreeNode:
    is_folder = item_is_folder(item)
    node: TreeNode = {
        "name": item_name(item),
        "fid": item_fid(item),
        "type": "folder" if is_folder else "file",
        "size": item_size(item),
    }
    if is_folder:
        node["children"] = []
    return node


def should_recurse(node: TreeNode, depth: int, max_depth: Optional[int]) -> bool:
    return node["type"] == "folder" and bool(node["fid"]) and (
        max_depth is None or depth < max_depth
    )


def iter_pages(fetch_page, page_size: int) -> Iterable[Dict[str, Any]]:
    page = 1
    fetched = 0
    while True:
        response = fetch_page(page, page_size)
        items = response_items(response)
        total = response_total(response)
        for item in items:
            yield item

        fetched += len(items)
        if not items:
            break
        if total is not None and fetched >= total:
            break
        if len(items) < page_size:
            break
        page += 1


def build_drive_tree(
    client: QuarkClient,
    folder_id: str,
    folder_name: str,
    page_size: int,
    max_depth: Optional[int],
    depth: int = 0,
) -> TreeNode:
    root: TreeNode = {
        "name": folder_name,
        "fid": folder_id,
        "type": "folder",
        "children": [],
    }

    def fetch_page(page: int, size: int) -> Dict[str, Any]:
        return client.list_files(folder_id=folder_id, page=page, size=size)

    for item in iter_pages(fetch_page, page_size):
        node = make_node(item)
        if should_recurse(node, depth + 1, max_depth):
            node = build_drive_tree(
                client=client,
                folder_id=node["fid"],
                folder_name=node["name"],
                page_size=page_size,
                max_depth=max_depth,
                depth=depth + 1,
            )
        root["children"].append(node)
    return root


def build_share_tree(
    client: QuarkClient,
    share_id: str,
    token: str,
    pdir_fid: str,
    folder_name: str,
    page_size: int,
    max_depth: Optional[int],
    depth: int = 0,
) -> TreeNode:
    root: TreeNode = {
        "name": folder_name,
        "fid": pdir_fid,
        "type": "folder",
        "children": [],
    }

    def fetch_page(page: int, size: int) -> Dict[str, Any]:
        return client.api_client.get(
            "share/sharepage/detail",
            params={
                "pwd_id": share_id,
                "stoken": token,
                "pdir_fid": pdir_fid,
                "force": "0",
                "_page": page,
                "_size": size,
                "_fetch_banner": "1",
                "_fetch_share": "1",
                "_fetch_total": "1",
                "_sort": "file_type:asc,file_name:asc",
            },
            base_url=Config.SHARE_BASE_URL,
        )

    for item in iter_pages(fetch_page, page_size):
        node = make_node(item)
        if should_recurse(node, depth + 1, max_depth):
            node = build_share_tree(
                client=client,
                share_id=share_id,
                token=token,
                pdir_fid=node["fid"],
                folder_name=node["name"],
                page_size=page_size,
                max_depth=max_depth,
                depth=depth + 1,
            )
        root["children"].append(node)
    return root


def print_tree(node: TreeNode, prefix: str = "") -> None:
    print(render_tree(node, prefix))


def render_tree(node: TreeNode, prefix: str = "") -> str:
    lines = [node["name"] or node["fid"] or "/"]
    children = node.get("children") or []
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        connector = "`-- " if is_last else "|-- "
        child_prefix = "    " if is_last else "|   "
        render_subtree(child, prefix + connector, prefix + child_prefix, lines)
    return "\n".join(lines)


def print_subtree(node: TreeNode, line_prefix: str, child_prefix: str) -> None:
    lines: List[str] = []
    render_subtree(node, line_prefix, child_prefix, lines)
    print("\n".join(lines))


def render_subtree(
    node: TreeNode,
    line_prefix: str,
    child_prefix: str,
    lines: List[str],
) -> None:
    name = node["name"] or node["fid"]
    if node["type"] == "folder":
        name += "/"
    lines.append(f"{line_prefix}{name}")

    children = node.get("children") or []
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        connector = "`-- " if is_last else "|-- "
        next_prefix = "    " if is_last else "|   "
        render_subtree(child, child_prefix + connector, child_prefix + next_prefix, lines)


def save_output(text: str, output_path: str) -> str:
    absolute_path = os.path.abspath(output_path)
    output_dir = os.path.dirname(absolute_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(absolute_path, "w", encoding="utf-8") as file:
        file.write(text)
        file.write("\n")
    return absolute_path


def resolve_drive_folder_id(client: QuarkClient, target: str) -> tuple[str, str]:
    if target == "0" or re.fullmatch(r"[A-Za-z0-9_-]+", target):
        return target, "root" if target == "0" else target

    fid, file_type = client.resolve_path(target)
    if file_type != "folder":
        raise ValueError(f"Target path is not a folder: {target}")
    return fid, target.rstrip("/").split("/")[-1] or target


def main() -> int:
    args = parse_args()
    page_size = max(1, min(args.page_size, 100))
    source = args.source
    if source == "auto":
        source = "share" if is_share_target(args.target) else "drive"

    client = QuarkClient(cookies=args.cookie, auto_login=(source == "drive" and not args.cookie))
    try:
        if source == "share":
            share_url, parsed_password = extract_share_url_and_password(args.target)
            password = args.password if args.password is not None else parsed_password
            share_id, parsed_by_client = client.parse_share_url(share_url)
            token = client.shares.get_share_token(
                share_id, password if password is not None else parsed_by_client
            )
            tree = build_share_tree(
                client=client,
                share_id=share_id,
                token=token,
                pdir_fid=args.pdir_fid,
                folder_name=share_id if args.pdir_fid == "0" else args.pdir_fid,
                page_size=page_size,
                max_depth=args.max_depth,
            )
        else:
            folder_id, folder_name = resolve_drive_folder_id(client, args.target)
            tree = build_drive_tree(
                client=client,
                folder_id=folder_id,
                folder_name=folder_name,
                page_size=page_size,
                max_depth=args.max_depth,
            )

        if args.json:
            output_text = json.dumps(tree, ensure_ascii=False, indent=2)
        else:
            output_text = render_tree(tree)

        print(output_text)
        saved_path = save_output(output_text, args.output)
        print(f"\nSaved to: {saved_path}")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
