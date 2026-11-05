from __future__ import annotations

import re
from pathlib import Path, PurePosixPath


class UnsafeVendorPathError(ValueError):
    pass


def safe_manifest_rel(raw_rel: str) -> str:
    rel = raw_rel.strip().replace("\\", "/")
    if rel in {"", "."} or rel.startswith("/") or re.match(r"^[A-Za-z]:/", rel):
        raise UnsafeVendorPathError(f"unsafe stata.trk path: {raw_rel}")
    if any(part in {"", ".", ".."} for part in rel.split("/")):
        raise UnsafeVendorPathError(f"unsafe stata.trk path: {raw_rel}")
    pure = PurePosixPath(rel)
    if pure.is_absolute():
        raise UnsafeVendorPathError(f"unsafe stata.trk path: {raw_rel}")
    return str(pure)


def safe_manifest_file(root: Path, raw_rel: str) -> Path:
    base = root.resolve()
    rel = safe_manifest_rel(raw_rel)
    current = base
    for part in PurePosixPath(rel).parts:
        current = current / part
        if current.is_symlink():
            raise UnsafeVendorPathError(f"stata.trk path uses symlink component: {raw_rel}")
    resolved = current.resolve(strict=False)
    if not _is_within(resolved, base):
        raise UnsafeVendorPathError(f"stata.trk path escapes vendor root: {raw_rel}")
    return resolved


def safe_vendor_target(package_copy: Path, vendor_dir: str, raw_rel: str) -> Path:
    rel = safe_manifest_rel(raw_rel)
    base = package_copy.resolve()
    target_rel = PurePosixPath(vendor_dir) / PurePosixPath(rel)
    current = base
    for part in target_rel.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise UnsafeVendorPathError(f"vendor destination uses symlink component: {raw_rel}")
    target = package_copy / Path(*target_rel.parts)
    resolved = target.resolve(strict=False)
    if not _is_within(resolved, base):
        raise UnsafeVendorPathError(f"vendor destination escapes root: {raw_rel}")
    return target


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False
