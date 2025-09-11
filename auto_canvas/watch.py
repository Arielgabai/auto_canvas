import os
import time
from typing import List

from .config import load_settings
from .utils import list_image_files, wait_until_stable, load_state, save_state, sort_by_ctime, file_signature, prune_state_absent_files
from .pipeline import process_batch


def collect_new_images() -> List[str]:
    settings = load_settings()
    state = load_state(settings.state_file)
    processed = set(state.get("processed", []))
    processed_signatures = state.get("processed_signatures", {})
    candidates = sort_by_ctime(list_image_files(settings.input_dir))
    new_files: List[str] = []
    changed = False
    for p in candidates:
        sig = file_signature(p)
        prev_sig = processed_signatures.get(p)
        if p not in processed:
            new_files.append(p)
            continue
        # p is in processed: ensure we have a baseline signature
        if not prev_sig and sig:
            processed_signatures[p] = sig
            changed = True
        # If signature changed since baseline, treat as new
        if prev_sig and sig and sig != prev_sig:
            new_files.append(p)
    if changed:
        state["processed_signatures"] = processed_signatures
        save_state(settings.state_file, state)
    return new_files


def run_watcher() -> None:
    settings = load_settings()
    print(f"Watching: {settings.input_dir} (batch={settings.batch_size})", flush=True)
    while True:
        try:
            # First, prune state for files no longer present, so re-copied files are treated as new
            current_files = sort_by_ctime(list_image_files(settings.input_dir))
            prune_state_absent_files(settings.state_file, current_files)

            new_files = collect_new_images()
            print(f"New files detected: {len(new_files)}", flush=True)
            if len(new_files) >= settings.batch_size:
                # Process as many full batches as available, always oldest first
                while True:
                    new_files = collect_new_images()
                    if len(new_files) < settings.batch_size:
                        break
                    print("Evaluating oldest batch of 9 for stability...", flush=True)
                    batch = new_files[: settings.batch_size]
                    stable = wait_until_stable(
                        batch,
                        stability_seconds=settings.stability_seconds,
                        check_interval=1.0,
                    )
                    print(f"Stable images: {len(stable)}/{settings.batch_size}", flush=True)
                    if len(stable) == settings.batch_size:
                        print("Batch ready. Processing...", flush=True)
                        try:
                            pdf = process_batch(stable)
                            print(f"Done: {pdf}", flush=True)
                        except Exception as e:
                            print(f"Pipeline error: {e}", flush=True)
                            # Stop inner loop to avoid busy retry; will retry next poll
                            break
                        # Loop again in case more than one batch is ready
                        continue
                    else:
                        # Oldest batch not stable yet; wait before retry
                        break
                print(f"Sleeping {settings.poll_interval_seconds}s...", flush=True)
                time.sleep(settings.poll_interval_seconds)
            else:
                # Not enough files yet
                print(f"Waiting for files... Sleeping {settings.poll_interval_seconds}s", flush=True)
                time.sleep(settings.poll_interval_seconds)
        except KeyboardInterrupt:
            print("Stopped by user.", flush=True)
            break
        except Exception as e:
            print(f"Error in watcher: {e}", flush=True)
            time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    run_watcher()


