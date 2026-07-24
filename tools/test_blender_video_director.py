import os
import sys
import tempfile
from types import SimpleNamespace

import bpy


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import nano_banana_render
from nano_banana_render import auth_utils, gemini_api, render_engine, texture_pipeline, video_director


VIDEO_PATH = os.path.join(REPO_ROOT, "docs", "videos", "1.mp4")


def main():
    nano_banana_render.register()
    scene = bpy.context.scene
    props = scene.nanode_video_director
    assert scene.gemini_render.omni_render_mode == "EEVEE"
    assert scene.gemini_render.omni_input_mode == "VIDEO_EDIT"
    assert scene.gemini_render.omni_duration == "10"
    assert scene.gemini_render.omni_aspect_ratio == "16:9"
    assert scene.gemini_render.use_style_reference is False
    scene.gemini_render.omni_aspect_ratio = "9:16"
    assert (scene.render.resolution_x, scene.render.resolution_y) == (720, 1280)
    assert render_engine.apply_omni_camera_aspect(scene, "unsupported") == "16:9"
    scene.gemini_render.omni_aspect_ratio = "16:9"
    assert (scene.render.resolution_x, scene.render.resolution_y) == (1280, 720)

    render_snapshot = texture_pipeline._store_render_settings(scene)
    output_snapshot = render_engine._store_omni_output_settings(scene)
    try:
        scene.render.image_settings.media_type = 'VIDEO'
        assert scene.render.image_settings.file_format == 'FFMPEG'
        render_engine._configure_omni_scene(
            scene,
            'WORKBENCH',
            1280,
            720,
            os.path.join(tempfile.gettempdir(), "nanode_omni_capture_test.png"),
        )
        assert scene.render.image_settings.media_type == 'IMAGE'
        assert scene.render.image_settings.file_format == 'PNG'
    finally:
        render_engine._restore_omni_output_settings(scene, output_snapshot)
        texture_pipeline._restore_render_settings(scene, render_snapshot)

    props.model = "gemini-omni-flash-preview"
    assert props.resolution == "720p"
    props.task = "edit"
    props.duration = "10"
    props.source_video_path = VIDEO_PATH
    assert video_director._model_validation_error(props) == ""
    assert video_director._effective_duration(props) == 10
    assert props.edit_duration == "AUTO"
    detected_duration = video_director._probe_video_duration_seconds(VIDEO_PATH)
    assert detected_duration > 0
    assert video_director._nearest_omni_duration(detected_duration) in {4, 6, 8, 10}
    props.detected_duration_path = ""
    props.detected_duration_seconds = 0.0
    assert video_director._detected_source_duration(props, allow_probe=False) == detected_duration
    assert props.detected_duration_path == ""
    assert props.detected_duration_seconds == 0.0
    video_director._assign_source_video(props, VIDEO_PATH)
    assert props.detected_duration_seconds == detected_duration

    props.model = "veo-3.1-lite-generate-preview"
    assert props.task == "text_to_video"
    assert props.duration != "10"

    image = bpy.data.images.new("AI_Result_Integration_Test", width=8, height=8)
    reference_export_dir = tempfile.mkdtemp(prefix="nanode_reference_export_test_")
    try:
        exported_reference = video_director._export_image(
            image,
            reference_export_dir,
            "style_reference.png",
        )
        with open(exported_reference, "rb") as exported_file:
            assert exported_file.read(8) == b"\x89PNG\r\n\x1a\n"
    finally:
        for filename in os.listdir(reference_export_dir):
            os.remove(os.path.join(reference_export_dir, filename))
        os.rmdir(reference_export_dir)
    props.use_style_reference = True
    props.style_reference_image = image
    style_prompt = video_director._build_video_edit_prompt("Make it look like polished clay", True)
    assert "<IMAGE_REF_0>@Image1" in style_prompt
    assert "purely for aesthetics" in style_prompt
    assert "BUT NOTHING ELSE" in style_prompt
    assert "DO_NOT_extract" in style_prompt
    assert "source video" in style_prompt
    omni_style_prompt = render_engine._build_omni_prompt(
        "Polished clay",
        "WORKBENCH",
        "video",
        0,
    )
    assert "<IMAGE_REF_0>@Image1" in omni_style_prompt
    assert "purely for aesthetics" in omni_style_prompt
    assert "BUT NOTHING ELSE" in omni_style_prompt
    assert "including capes, coats" in omni_style_prompt
    assert "wardrobe" in omni_style_prompt
    timeline_style_prompt = render_engine._build_omni_prompt(
        "Polished clay",
        "WORKBENCH",
        "image_sequence",
        2,
    )
    assert "<IMAGE_REF_2>@Image4" in timeline_style_prompt
    photo_style_prompt = gemini_api.GeminiAPI._build_prompt(
        None,
        "Polished clay",
        has_reference=True,
        is_color_render=True,
    )
    shared_rule = gemini_api._style_reference_aesthetics_rule("image_2")
    assert shared_rule in photo_style_prompt
    assert shared_rule.replace("image_2", "Image1") in style_prompt

    gemini_props = scene.gemini_render
    gemini_props.use_style_reference = True
    gemini_props.style_reference_image = image
    gemini_props.omni_input_mode = "VIDEO_EDIT"
    original_capture_video = render_engine._capture_omni_video
    original_export_image = video_director._export_image
    try:
        render_engine._capture_omni_video = lambda *_args: {
            "path": VIDEO_PATH,
            "reference_paths": [],
            "media_type": "video",
            "source_mode": "WORKBENCH",
            "input_mode": "VIDEO_EDIT",
            "temp_dir": tempfile.gettempdir(),
        }
        video_director._export_image = lambda *_args: os.path.join(
            tempfile.gettempdir(),
            "omni_style_reference.png",
        )
        capture = render_engine._prepare_omni_capture(scene, gemini_props)
        assert capture["style_reference_index"] == 0
        assert capture["reference_paths"][-1].endswith("omni_style_reference.png")
    finally:
        render_engine._capture_omni_video = original_capture_video
        video_director._export_image = original_export_image
    direct_reference = os.path.join(tempfile.gettempdir(), "nanode_direct_style_reference.png")
    with open(direct_reference, "wb") as reference_file:
        reference_file.write(b"\x89PNG\r\n\x1a\n" + b"0" * 256)
    captured = {}

    class FakeInteractions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return {
                "id": "direct-style-test",
                "steps": [{"content": [{"type": "video", "data": "AAAAHGZ0eXBpc29t"}]}],
            }

    class FakeFiles:
        def delete(self, **_kwargs):
            pass

    original_genai_available = gemini_api.GENAI_AVAILABLE
    had_genai = hasattr(gemini_api, "genai")
    original_genai = getattr(gemini_api, "genai", None)
    original_upload = gemini_api._upload_omni_file_sdk
    try:
        gemini_api.GENAI_AVAILABLE = True
        gemini_api.genai = SimpleNamespace(
            Client=lambda api_key: SimpleNamespace(interactions=FakeInteractions(), files=FakeFiles())
        )
        gemini_api._upload_omni_file_sdk = lambda client, path: SimpleNamespace(
            uri="files/source-video",
            name="files/source-video",
        )
        _video_bytes, direct_interaction_id = gemini_api.generate_omni_video_direct(
            api_key="AQ.test-key",
            prompt=style_prompt,
            task="edit",
            aspect_ratio="16:9",
            duration_seconds=10,
            reference_image_paths=[direct_reference],
            video_path=VIDEO_PATH,
            match_source_duration=True,
        )
        assert direct_interaction_id == "direct-style-test"
        assert [part["type"] for part in captured["input"]] == ["document", "image", "text"]
        assert "duration" not in captured["response_format"]
    finally:
        gemini_api.GENAI_AVAILABLE = original_genai_available
        if had_genai:
            gemini_api.genai = original_genai
        else:
            del gemini_api.genai
        gemini_api._upload_omni_file_sdk = original_upload
        os.remove(direct_reference)
    item = scene.gemini_render.render_history.add()
    item.image_name = image.name
    resolved = video_director._latest_render_history_image(scene)
    assert resolved == image
    generic = bpy.data.images.get("Render Result") or bpy.data.images.new("Render Result", width=8, height=8)
    assert video_director._resolve_editor_image(bpy.context, generic) == image
    assert auth_utils.is_google_api_key("AQ." + ("test-only-" * 3))
    fake_video, interaction_id = gemini_api._extract_omni_video(
        {"id": "interaction-test", "steps": [{"content": [{"type": "video", "data": "AAAAHGZ0eXBpc29t"}]}]}
    )
    assert fake_video[4:8] == b"ftyp"
    assert interaction_id == "interaction-test"

    assert os.path.isfile(VIDEO_PATH)
    loaded_path = video_director.load_video_path_to_sequencer(
        VIDEO_PATH,
        9191,
        "Nanode Integration",
        scene.name,
    )
    assert loaded_path == VIDEO_PATH
    assert scene.render.use_sequencer is False
    strips = video_director._all_sequence_strips(scene.sequence_editor)
    assert any(strip.type == "MOVIE" for strip in strips)
    assert any(strip.type == "SOUND" for strip in strips)
    assert props.last_video_path == VIDEO_PATH
    continuation_model = "veo-3.1-fast-generate-preview"
    props.model = continuation_model
    continuation_frame = scene.frame_current
    assert bpy.ops.nanode.video_continue_from_playhead() == {'FINISHED'}
    assert props.model == continuation_model
    assert props.task == "image_to_video"
    assert props.input_image is not None
    assert props.input_image.packed_file is not None
    assert props.continuation_source_frame == continuation_frame
    assert scene.render.use_sequencer is False
    for strip in strips:
        strip.select = strip.type == "MOVIE"
    props.source_video_path = ""
    assert bpy.ops.nanode.video_use_selected_strip() == {'FINISHED'}
    assert os.path.normcase(props.source_video_path) == os.path.normcase(VIDEO_PATH)
    assert bpy.types.Panel.bl_rna_get_subclass_py("NANODE_PT_video_editor_sequencer") is not None
    assert bpy.types.Panel.bl_rna_get_subclass_py("NANODE_PT_video_editor_input") is not None
    assert bpy.types.Panel.bl_rna_get_subclass_py("BANANA_PT_omni_style_reference") is not None

    preview_window = bpy.context.window_manager.windows[0]
    preview_area = next(area for area in preview_window.screen.areas if area.type == 'VIEW_3D')
    preview_area.type = 'IMAGE_EDITOR'
    preview_area.spaces.active.image = generic
    located_preview = video_director._render_preview_area()
    assert located_preview is not None
    assert located_preview[0] == preview_window
    assert located_preview[1] == preview_area
    video_director._configure_preview_area(preview_window, preview_area, scene)
    assert preview_area.type == 'SEQUENCE_EDITOR'
    assert preview_area.spaces.active.view_type == 'SEQUENCER_PREVIEW'
    assert preview_window.scene == scene
    assert scene.sequence_editor.active_strip is not None
    assert scene.sequence_editor.active_strip.type == 'MOVIE'
    try:
        del preview_window.screen[video_director._PREVIEW_SCREEN_KEY]
    except KeyError:
        pass
    preview_area.type = 'VIEW_3D'

    area_types = [area.type for window in bpy.context.window_manager.windows for area in window.screen.areas]
    video_director._show_video_preview(scene.name)
    assert [area.type for window in bpy.context.window_manager.windows for area in window.screen.areas] == area_types

    entry = video_director.record_video_job(
        scene,
        {
            "id": 9191,
            "model": "gemini-omni-flash-preview",
            "task": "edit",
            "status": "succeeded",
            "duration_seconds": 10,
            "resolution": "720p",
            "aspect_ratio": "16:9",
            "reserved_credits": 240,
            "user_prompt": "Polished clay hero",
            "source_video_path": VIDEO_PATH,
            "style_reference_name": image.name,
        },
        source="OMNI_ENGINE",
        filepath=VIDEO_PATH,
    )
    assert entry is not None
    assert entry.filepath == VIDEO_PATH
    assert entry.prompt == "Polished clay hero"
    assert entry.source_video_path == VIDEO_PATH
    assert len(props.video_history) == 1
    scheduled_editor = {}
    original_schedule_editor = video_director._schedule_video_editor
    try:
        video_director._schedule_video_editor = lambda scene_name, strip_name: scheduled_editor.update(
            scene_name=scene_name,
            strip_name=strip_name,
        )
        assert bpy.ops.nanode.video_history_play(history_index=0) == {'FINISHED'}
    finally:
        video_director._schedule_video_editor = original_schedule_editor
    assert scheduled_editor["scene_name"] == scene.name
    assert scheduled_editor["strip_name"] == "Nanode History #9191"
    assert os.path.normcase(props.source_video_path) == os.path.normcase(VIDEO_PATH)
    video_director._focus_video_editor(
        preview_window,
        scene,
        scheduled_editor["strip_name"],
    )
    assert any(area.type == 'SEQUENCE_EDITOR' for area in preview_window.screen.areas)
    assert scene.sequence_editor.active_strip.name == "Nanode History #9191"
    assert bpy.ops.nanode.video_history_reuse_omni(history_index=0) == {'FINISHED'}
    assert scene.render.engine == 'NANODE_OMNI'
    assert scene.gemini_render.omni_source_video_override == VIDEO_PATH
    assert scene.gemini_render.prompt == "Polished clay hero"

    blend_path = os.path.join(tempfile.gettempdir(), "nanode_video_history_roundtrip.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    reopened = bpy.context.scene.nanode_video_director
    assert len(reopened.video_history) == 1
    assert reopened.video_history[0].filepath == VIDEO_PATH
    assert reopened.video_history[0].source_video_path == VIDEO_PATH
    assert bpy.context.scene.gemini_render.omni_source_video_override == VIDEO_PATH
    assert bpy.context.scene.gemini_render.omni_duration == "10"
    assert reopened.style_reference_image.name == "AI_Result_Integration_Test"
    os.remove(blend_path)

    nano_banana_render.unregister()
    print("BLENDER_VIDEO_DIRECTOR_OK")


main()
