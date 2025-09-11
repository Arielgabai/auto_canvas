import os
import time
from typing import List

from .config import load_settings
from .gdrive import list_images_in_folder, download_file, upload_file
from .utils import load_state, save_state, file_signature
from .pipeline import process_batch


def run_gdrive_watcher() -> None:
    s = load_settings()
    input_folder_id = os.getenv("GDRIVE_INPUT_FOLDER_ID", "")
    output_folder_id = os.getenv("GDRIVE_OUTPUT_FOLDER_ID", "")
    if not input_folder_id or not output_folder_id:
        raise RuntimeError("GDRIVE_INPUT_FOLDER_ID and GDRIVE_OUTPUT_FOLDER_ID must be set")

    print(f"Watching Google Drive folder: {input_folder_id} (batch={s.batch_size})", flush=True)
    while True:
        try:
            images = list_images_in_folder(input_folder_id)
            # Map to local staging paths by id
            todo_ids: List[str] = []

            # Load state (keep processed Drive file ids)
            st = load_state(s.state_file)
            processed_ids = set(st.get("processed_drive_ids", []))

            for f in images:
                fid = f["id"]
                if fid in processed_ids:
                    continue
                todo_ids.append(fid)

            if len(todo_ids) >= s.batch_size:
                batch_ids = todo_ids[: s.batch_size]
                local_paths: List[str] = []
                for fid in batch_ids:
                    dest = os.path.join(s.input_dir, f"gdrive_{fid}.bin")
                    print(f"Downloading {fid} -> {dest}", flush=True)
                    download_file(fid, dest)
                    local_paths.append(dest)

                pdf = process_batch(local_paths)
                print(f"Done: {pdf}", flush=True)

                # Upload result PDF
                print(f"Uploading PDF to Drive folder: {output_folder_id}", flush=True)
                upload_file(pdf, output_folder_id, mime_type="application/pdf")

                # Mark processed ids
                processed_ids.update(batch_ids)
                st["processed_drive_ids"] = sorted(processed_ids)
                save_state(s.state_file, st)
            else:
                print(f"Waiting for files... Sleeping {s.poll_interval_seconds}s", flush=True)
                time.sleep(s.poll_interval_seconds)
        except KeyboardInterrupt:
            print("Stopped by user.", flush=True)
            break
        except Exception as e:
            print(f"Error in gdrive watcher: {e}", flush=True)
            time.sleep(s.poll_interval_seconds)


if __name__ == "__main__":
    run_gdrive_watcher()


