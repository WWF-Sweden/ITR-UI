"""
Layout helpers for the Streamlit UI: asset resolution and hero rendering.
These functions use importlib.resources when possible and fall back to
filesystem paths (useful in development).
"""
import os
import base64
from pathlib import Path
from importlib import resources
import streamlit as st
from typing import Optional


def get_local_asset(package: str, rel_path: str) -> Optional[str]:
    """
    Return a filesystem path to an asset packaged under `package`/`rel_path`,
    or None if not found.

    - package: importable package name (e.g. "app")
    - rel_path: path inside package (POSIX style) e.g. "static/panda.jpeg"
    """
    # Try importlib.resources (works with installed packages/wheels)
    try:
        res = resources.files(package).joinpath(rel_path)
        if getattr(res, "exists", lambda: False)():
            with resources.as_file(res) as p:
                return str(p)
    except Exception:
        pass

    # Fallback: path relative to this package's source (development)
    try:
        # assume this module lives in the same package as the asset
        caller_dir = Path(__file__).resolve().parent
        candidate = caller_dir.joinpath(rel_path)
        if candidate.exists():
            return str(candidate)
    except Exception:
        pass

    return None


def render_hero(title: str, subtitle: str, img_path: Optional[str], img_height: int = 80):
    """
    Render a hero banner: text on the left, optional image on the right.
    - img_path: filesystem path to image or None to render without image
    - img_height: pixel height for the image
    """
    img_html = ""
    if img_path and os.path.exists(img_path):
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        img_html = (
            f'<img src="data:image/jpeg;base64,{b64}" '
            f'style="height:{img_height}px; margin-left:16px; border-radius:8px; object-fit:contain;" />'
        )

    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:16px; padding:0.5rem 1rem;">
          <div style="flex:1;">
            <h1 style="margin:0; font-size:28px;">{title}</h1>
            <p style="margin:0.35rem 0 0; color:#444; font-size:16px;">{subtitle}</p>
          </div>
          <div style="flex:0 0 auto;">{img_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_icon_path() -> Optional[str]:
    """
    Convenience: look for app/static/panda.jpeg then app/static/ITR-logo.png.
    Return filesystem path or None.
    """
    for p in ("static/panda.jpeg", "static/panda.jpg", "static/ITR-logo.png"):
        found = get_local_asset("app", p)
        if found:
            return found
    return None