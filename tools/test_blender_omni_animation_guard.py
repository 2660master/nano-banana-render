import os
import sys

import bpy


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import nano_banana_render
from nano_banana_render import beta_api, render_engine


def main():
    nano_banana_render.register()
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 3
    scene.gemini_render.prompt = "Preserve this scene and render the existing animation."

    video_calls = []
    image_calls = []
    original_create_video_job = beta_api.create_video_job
    original_generate = beta_api.generate
    beta_api.create_video_job = lambda **kwargs: video_calls.append(kwargs)
    beta_api.generate = lambda **kwargs: image_calls.append(kwargs)
    try:
        for engine in ("NANODE_OMNI", "NANO_BANANA"):
            scene.render.engine = engine
            try:
                bpy.ops.render.render(animation=True)
            except RuntimeError:
                pass
    finally:
        beta_api.create_video_job = original_create_video_job
        beta_api.generate = original_generate

    assert not video_calls, f"Animation render submitted {len(video_calls)} paid video jobs"
    assert not image_calls, f"Animation render submitted {len(image_calls)} paid image jobs"
    assert "Render Animation is disabled" in scene.gemini_render.omni_status
    assert "Render Animation is disabled" in scene.gemini_render.status_text
    assert not render_engine._omni_submission_active
    assert not render_engine._omni_autotrigger_pending
    render_engine._omni_last_submission_finished_at = 0.0
    assert render_engine._begin_omni_submission()
    assert not render_engine._begin_omni_submission()
    render_engine._finish_omni_submission()
    assert not render_engine._begin_omni_submission()
    assert scene.frame_current == scene.frame_start
    print("BLENDER_OMNI_ANIMATION_GUARD_OK")


if __name__ == "__main__":
    main()
