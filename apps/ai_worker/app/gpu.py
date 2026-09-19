"""GPU info for /health via nvidia-smi (no torch dependency; None when no CUDA GPU)."""

import shutil
import subprocess


def gpu_info() -> dict[str, str | int] | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        ).stdout
        name, mem = out.strip().splitlines()[0].split(",")
        return {"name": name.strip(), "mem_used_mb": int(float(mem))}
    except (subprocess.SubprocessError, ValueError, IndexError):
        return None
