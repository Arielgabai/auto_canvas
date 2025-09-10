import json
import os
import time
from typing import Dict, List, Tuple


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def is_image_file(path: str) -> bool:
    _, ext = os.path.splitext(path.lower())
    return ext in IMAGE_EXTENSIONS


def list_image_files(directory: str) -> List[str]:
    if not os.path.isdir(directory):
        return []
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and is_image_file(f)
    ]


def sort_by_ctime(paths: List[str]) -> List[str]:
    return sorted(paths, key=lambda p: os.path.getctime(p))


def file_signature(path: str) -> str:
    """Signature d'un fichier: taille + mtime + ctime pour distinguer réapparitions et duplications."""
    try:
        st = os.stat(path)
        return f"{st.st_size}:{int(st.st_mtime)}:{int(getattr(st, 'st_ctime', st.st_mtime))}"
    except FileNotFoundError:
        return ""


def load_state(state_file: str) -> Dict:
    if not os.path.exists(state_file):
        return {"processed": [], "processing": [], "processed_signatures": {}}
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
            # Backward-compatible defaults
            if "processed" not in state:
                state["processed"] = []
            if "processing" not in state:
                state["processing"] = []
            if "processed_signatures" not in state:
                state["processed_signatures"] = {}
            return state
    except Exception:
        return {"processed": [], "processing": [], "processed_signatures": {}}


def save_state(state_file: str, state: Dict) -> None:
    tmp = state_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, state_file)


def wait_until_stable(
    paths: List[str], stability_seconds: int = 3, check_interval: float = 1.0
) -> List[str]:
    """Return subset of paths that are stable (size unchanged for stability_seconds)."""
    now = time.time()
    initial_sizes: Dict[str, Tuple[int, float]] = {}
    for p in paths:
        try:
            initial_sizes[p] = (os.path.getsize(p), now)
        except FileNotFoundError:
            continue

    time.sleep(check_interval)

    stable: List[str] = []
    for p in paths:
        try:
            size1, t0 = initial_sizes.get(p, (None, None))
            size2 = os.path.getsize(p)
            if size1 is not None and size1 == size2:
                # Passed first check; wait remaining time
                remaining = max(0.0, stability_seconds - check_interval)
                time.sleep(remaining)
                size3 = os.path.getsize(p)
                if size3 == size2:
                    stable.append(p)
        except FileNotFoundError:
            continue
    return stable


def chunk(items: List[str], n: int) -> List[List[str]]:
    return [items[i : i + n] for i in range(0, len(items), n)]


def file_basename_without_ext(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def prune_state_absent_files(state_file: str, existing_files: List[str]) -> None:
    """Remove entries from state for files that no longer exist in INPUT_DIR.

    This allows a later re-copy of the same filename to be considered NEW again.
    """
    existing_set = set(existing_files)
    state = load_state(state_file)
    changed = False

    processed = state.get("processed", [])
    new_processed = [p for p in processed if p in existing_set]
    if new_processed != processed:
        state["processed"] = new_processed
        changed = True

    processing = state.get("processing", [])
    new_processing = [p for p in processing if p in existing_set]
    if new_processing != processing:
        state["processing"] = new_processing
        changed = True

    processed_signatures = state.get("processed_signatures", {})
    new_signatures = {
        p: sig for p, sig in processed_signatures.items() if p in existing_set
    }
    if new_signatures != processed_signatures:
        state["processed_signatures"] = new_signatures
        changed = True

    if changed:
        save_state(state_file, state)

