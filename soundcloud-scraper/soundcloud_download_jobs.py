from __future__ import annotations

import threading
import uuid
from urllib.parse import urlparse


DOWNLOAD_PROGRESS_SCRIPT = r"""
  window.downloadProfileSelected = async function() {
    const indexes = [...document.querySelectorAll('#profile-body input:checked')].map(box => Number(box.dataset.index));
    if (!indexes.length) {
      setStatus('Select at least one song.', true);
      return;
    }
    const button = document.querySelector('button[onclick="downloadProfileSelected()"]');
    if (button) button.disabled = true;
    try {
      const started = await api('/api/download/start', {tracks:indexes.map(index => profileTracks[index])});
      setStatus(`Download started for ${indexes.length} song(s). Keep this window open.`);
      while (true) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        const progress = await api('/api/download/status', {job_id:started.job_id});
        setStatus(progress.message, progress.state === 'failed');
        if (progress.state === 'complete' || progress.state === 'failed') break;
      }
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      if (button) button.disabled = false;
    }
  };
"""


def install_download_jobs(app) -> None:
    jobs: dict[str, dict] = {}
    lock = threading.Lock()
    original_post = app.Handler.do_POST

    def snapshot(job_id: str) -> dict:
        with lock:
            job = jobs.get(job_id)
            if not job:
                raise RuntimeError("That download job could not be found.")
            return dict(job)

    def update(job_id: str, **values) -> None:
        with lock:
            jobs[job_id].update(values)

    def run_job(job_id: str, tracks: list[dict]) -> None:
        completed = skipped = failed = 0
        errors = []
        try:
            env = app.build_env()
            app.ensure_dependencies(env)
            for index, track in enumerate(tracks, start=1):
                title = track.get("title") or track.get("track_url") or f"Track {index}"
                update(
                    job_id,
                    message=f"Downloading {index} of {len(tracks)}: {title}",
                    current=index,
                )
                result = app.download_track(
                    track.get("track_url", ""),
                    env,
                    app.OUTPUT_FOLDER,
                    "easy",
                    track_info=track,
                )
                if result.status == "completed":
                    completed += 1
                elif result.status == "skipped":
                    skipped += 1
                else:
                    failed += 1
                    if result.error:
                        errors.append(f"{title}: {result.error.splitlines()[-1]}")
            details = f"Finished. Downloaded {completed}, skipped {skipped}, failed {failed}."
            if errors:
                details += "\n" + "\n".join(errors[-3:])
            update(
                job_id,
                state="complete" if completed or skipped or not failed else "failed",
                message=details,
                completed=completed,
                skipped=skipped,
                failed=failed,
            )
        except Exception as exc:
            update(job_id, state="failed", message=f"Download stopped: {exc}")

    def do_post_with_jobs(handler):
        path = urlparse(handler.path).path
        if path == "/api/download/start":
            payload = app.read_json(handler)
            tracks = payload.get("tracks") or []
            if not tracks:
                raise RuntimeError("Select at least one song.")
            job_id = uuid.uuid4().hex
            with lock:
                jobs[job_id] = {
                    "job_id": job_id,
                    "state": "running",
                    "message": f"Starting download for {len(tracks)} song(s)...",
                    "current": 0,
                    "total": len(tracks),
                    "completed": 0,
                    "skipped": 0,
                    "failed": 0,
                }
            threading.Thread(target=run_job, args=(job_id, tracks), daemon=True).start()
            return app.json_response(handler, {"job_id": job_id, "status": "Download started."})
        if path == "/api/download/status":
            payload = app.read_json(handler)
            job = snapshot(payload.get("job_id", ""))
            job["status"] = "Downloading" if job["state"] == "running" else "Ready"
            return app.json_response(handler, job)
        return original_post(handler)

    app.Handler.do_POST = do_post_with_jobs
    app.HTML = app.HTML.replace("</script>", DOWNLOAD_PROGRESS_SCRIPT + "\n</script>", 1)
