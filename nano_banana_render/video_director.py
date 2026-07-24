from __future__ import annotations

import os
import shutil
import tempfile
import time
import uuid

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Operator, Panel, PropertyGroup
from bpy_extras.io_utils import ImportHelper

from . import auth_utils, beta_api, gemini_api
from .model_config import (
    OMNI_DURATION_ITEMS,
    VIDEO_EDIT_DURATION_ITEMS,
    VIDEO_DIRECTOR_TASK_ITEMS,
    VIDEO_MODEL_ITEMS,
    VIDEO_ASPECT_ITEMS,
    VIDEO_RESOLUTION_ITEMS,
    get_video_cost,
    is_omni_model,
)

_TARGET_PROPERTIES = {
    'FIRST': 'input_image',
    'LAST': 'last_frame_image',
    'REFERENCE_1': 'reference_image',
    'REFERENCE_2': 'reference_image_2',
    'REFERENCE_3': 'reference_image_3',
    'STYLE': 'style_reference_image',
}
_polling_job_ids: set[int] = set()
_runtime_generation = 0
_history_enum_cache = []
_PREVIEW_SCREEN_KEY = "nanode_video_preview"
_SUPPORTED_OMNI_DURATIONS = (4, 6, 8, 10)
_duration_cache: dict[str, float] = {}


def _probe_video_duration_seconds(filepath: str) -> float:
    filepath = bpy.path.abspath(filepath or "")
    if not filepath or not os.path.isfile(filepath):
        raise RuntimeError("Source video file is missing")

    normalized = os.path.normcase(os.path.abspath(filepath))
    cached = _duration_cache.get(normalized, 0.0)
    if cached > 0.0:
        return cached
    existing = next(
        (
            clip
            for clip in bpy.data.movieclips
            if os.path.normcase(os.path.abspath(bpy.path.abspath(clip.filepath))) == normalized
        ),
        None,
    )
    clip = existing or bpy.data.movieclips.load(filepath, check_existing=True)
    try:
        fps = float(getattr(clip, "fps", 0.0) or 0.0)
        frames = int(getattr(clip, "frame_duration", 0) or 0)
        if fps <= 0.0 or frames <= 0:
            raise RuntimeError("Blender could not read the source video duration")
        duration = frames / fps
        _duration_cache[normalized] = duration
        return duration
    finally:
        if existing is None and clip.users == 0:
            bpy.data.movieclips.remove(clip)


def _nearest_omni_duration(duration_seconds: float) -> int:
    return min(_SUPPORTED_OMNI_DURATIONS, key=lambda value: abs(value - duration_seconds))


def _detected_source_duration(props, allow_probe: bool = True) -> float:
    filepath = bpy.path.abspath(props.source_video_path or "")
    if not filepath:
        return 0.0
    normalized = os.path.normcase(os.path.abspath(filepath))
    if props.detected_duration_path == normalized and props.detected_duration_seconds > 0.0:
        return float(props.detected_duration_seconds)
    duration = _duration_cache.get(normalized, 0.0)
    if duration <= 0.0 and allow_probe:
        duration = _probe_video_duration_seconds(filepath)
    if duration <= 0.0:
        return 0.0
    if allow_probe:
        props.detected_duration_path = normalized
        props.detected_duration_seconds = duration
    return duration


def _assign_source_video(props, filepath: str) -> float:
    filepath = bpy.path.abspath(filepath or "")
    props.source_video_path = filepath
    props.detected_duration_path = ""
    props.detected_duration_seconds = 0.0
    if not filepath or not os.path.isfile(filepath):
        return 0.0
    return _detected_source_duration(props)


def _effective_edit_duration(props, allow_probe: bool = True) -> int:
    if props.edit_duration != "AUTO":
        return int(props.edit_duration)
    detected = _detected_source_duration(props, allow_probe=allow_probe)
    if detected <= 0.0:
        raise RuntimeError("Source duration has not been detected yet")
    return _nearest_omni_duration(detected)


def _edit_duration_validation_error(props, allow_probe: bool = True) -> str:
    if props.edit_duration == "AUTO" or not os.path.isfile(bpy.path.abspath(props.source_video_path)):
        return ""
    try:
        duration = _detected_source_duration(props, allow_probe=allow_probe)
        if duration <= 0.0:
            return ""
        detected = _nearest_omni_duration(duration)
    except Exception:
        return ""
    selected = int(props.edit_duration)
    if selected != detected:
        return f"Source is {detected}s; choose {detected}s or Auto"
    return ""


def _video_task_items(props, _context):
    if is_omni_model(getattr(props, "model", "")):
        allowed = {'auto', 'text_to_video', 'image_to_video', 'reference_to_video', 'edit'}
    elif getattr(props, "model", "") == 'veo-3.1-lite-generate-preview':
        allowed = {'text_to_video', 'image_to_video'}
    else:
        allowed = {'text_to_video', 'image_to_video', 'first_last', 'reference_to_video'}
    return [item for item in VIDEO_DIRECTOR_TASK_ITEMS if item[0] in allowed]


def _video_resolution_items(props, _context):
    model = getattr(props, "model", "")
    if is_omni_model(model):
        allowed = {'720p'}
    elif model == 'veo-3.1-lite-generate-preview':
        allowed = {'720p', '1080p'}
    else:
        allowed = {'720p', '1080p', '4k'}
    return [item for item in VIDEO_RESOLUTION_ITEMS if item[0] in allowed]


def _video_duration_items(props, _context):
    items = OMNI_DURATION_ITEMS if is_omni_model(getattr(props, "model", "")) else OMNI_DURATION_ITEMS[:3]
    return [(identifier, label, description, int(identifier)) for identifier, label, description in items]


def _on_model_changed(props, _context) -> None:
    task_value = int(props.get("task", 1))
    resolution_value = int(props.get("resolution", 0))
    duration_value = int(props.get("duration", 4))
    if is_omni_model(props.model):
        if resolution_value != 0:
            props.resolution = '720p'
        if task_value == 3:
            props.task = 'image_to_video'
    else:
        if task_value in {0, 5}:
            props.task = 'text_to_video'
        if props.model == 'veo-3.1-lite-generate-preview' and resolution_value == 2:
            props.resolution = '1080p'
        if duration_value == 10:
            props.duration = '8'


def _on_task_changed(props, _context) -> None:
    task_value = int(props.get("task", 1))
    if task_value == 3:
        props.duration = '8'
    if task_value == 4 and not is_omni_model(props.model):
        props.duration = '8'
    if task_value != 5:
        props.match_source_duration = False


class VideoHistoryItem(PropertyGroup):
    entry_id: StringProperty(name="Entry ID", default="")
    job_id: IntProperty(name="Job ID", default=0)
    source: StringProperty(name="Source", default="DIRECTOR")
    model: StringProperty(name="Model", default="")
    task: StringProperty(name="Mode", default="")
    status: StringProperty(name="Status", default="queued")
    filepath: StringProperty(name="File", default="", subtype='FILE_PATH')
    output_url: StringProperty(name="Output URL", default="")
    created_at: StringProperty(name="Created", default="")
    duration_seconds: IntProperty(name="Duration", default=0)
    resolution: StringProperty(name="Resolution", default="")
    aspect_ratio: StringProperty(name="Aspect", default="")
    credit_cost: IntProperty(name="Credits", default=0)
    error: StringProperty(name="Error", default="")
    prompt: StringProperty(name="Prompt", default="", maxlen=4000)
    source_video_path: StringProperty(name="Source Video", default="", subtype='FILE_PATH')
    style_reference_name: StringProperty(name="Style Reference", default="")


class VideoDirectorProperties(PropertyGroup):
    prompt: StringProperty(
        name="Prompt",
        description="Describe the video, motion, camera, and sound",
        default="",
        maxlen=1200,
    )
    task: EnumProperty(
        name="Mode",
        description="Video generation workflow",
        items=_video_task_items,
        default=1,
        update=_on_task_changed,
    )
    model: EnumProperty(
        name="Model",
        description="Video generation model",
        items=VIDEO_MODEL_ITEMS,
        default='veo-3.1-fast-generate-preview',
        update=_on_model_changed,
    )
    resolution: EnumProperty(
        name="Resolution",
        description="Output resolution",
        items=_video_resolution_items,
        default=0,
    )
    aspect_ratio: EnumProperty(
        name="Aspect",
        description="Output aspect ratio",
        items=VIDEO_ASPECT_ITEMS,
        default='16:9',
    )
    duration: EnumProperty(
        name="Duration",
        description="Output duration",
        items=_video_duration_items,
        default=4,
    )
    input_image: PointerProperty(
        type=bpy.types.Image,
        name="First Frame",
        description="Starting frame for image-to-video or interpolation",
    )
    last_frame_image: PointerProperty(
        type=bpy.types.Image,
        name="Last Frame",
        description="Ending frame for interpolation",
    )
    reference_image: PointerProperty(
        type=bpy.types.Image,
        name="Reference 1",
        description="First subject or product reference",
    )
    reference_image_2: PointerProperty(
        type=bpy.types.Image,
        name="Reference 2",
        description="Second subject or product reference",
    )
    reference_image_3: PointerProperty(
        type=bpy.types.Image,
        name="Reference 3",
        description="Third subject or product reference",
    )
    use_style_reference: BoolProperty(
        name="Style Reference",
        description="Use one image only for the edited video's visual style",
        default=False,
    )
    style_reference_image: PointerProperty(
        type=bpy.types.Image,
        name="Style Reference",
        description="Lighting, materials, texture, palette, and grading reference",
    )
    edit_duration: EnumProperty(
        name="Duration",
        description="Edited video duration",
        items=VIDEO_EDIT_DURATION_ITEMS,
        default='AUTO',
    )
    edit_aspect_ratio: EnumProperty(
        name="Aspect",
        description="Edited video aspect ratio",
        items=VIDEO_ASPECT_ITEMS,
        default='16:9',
    )
    source_video_path: StringProperty(
        name="Source Video",
        description="Video used by Omni Edit Video",
        default="",
        subtype='FILE_PATH',
    )
    detected_duration_seconds: FloatProperty(default=0.0, options={'HIDDEN'})
    detected_duration_path: StringProperty(default="", options={'HIDDEN'})
    match_source_duration: BoolProperty(default=False, options={'HIDDEN'})
    continuation_source_frame: IntProperty(default=0, options={'HIDDEN'})
    last_video_path: StringProperty(name="Last Video", default="", options={'HIDDEN'})
    status: StringProperty(name="Status", default="Ready")
    last_job_id: IntProperty(name="Last Job ID", default=0)
    loaded_job_id: IntProperty(name="Loaded Job ID", default=0, options={'HIDDEN'})
    output_url: StringProperty(name="Output URL", default="", options={'HIDDEN'})
    video_history: CollectionProperty(type=VideoHistoryItem)
    show_video_history: BoolProperty(name="Video History", default=True)


def _get_configured_token(context) -> str:
    addon = context.preferences.addons.get("nano_banana_render")
    if not addon or not hasattr(addon.preferences, "beta_token"):
        return ""
    token = addon.preferences.beta_token.strip()
    if auth_utils.is_nanode_token(token) or auth_utils.is_google_api_key(token):
        return token
    return ""


def _get_nanode_token(context) -> str:
    token = _get_configured_token(context)
    return token if auth_utils.is_nanode_token(token) else ""


def _video_props(context):
    scene = getattr(context, "scene", None)
    return getattr(scene, "nanode_video_director", None) if scene else None


def _video_entry_id(job: dict) -> str:
    explicit = str(job.get("entry_id") or "")
    if explicit:
        return explicit
    job_id = int(job.get("id") or job.get("job_id") or 0)
    return f"job:{job_id}" if job_id else ""


def record_video_job(scene, job: dict, source: str = "DIRECTOR", filepath: str = ""):
    props = getattr(scene, "nanode_video_director", None) if scene else None
    if not props:
        return None
    entry_id = _video_entry_id(job)
    if not entry_id:
        return None

    entry = next((item for item in props.video_history if item.entry_id == entry_id), None)
    if entry is None:
        entry = props.video_history.add()
        entry.entry_id = entry_id
        entry.source = source
    elif source and entry.source in {"", "SERVER"}:
        entry.source = source

    entry.job_id = int(job.get("id") or job.get("job_id") or entry.job_id or 0)
    entry.model = str(job.get("model") or entry.model or "")
    entry.task = str(job.get("task") or entry.task or "")
    entry.status = str(job.get("status") or entry.status or "queued")
    entry.output_url = str(job.get("output_url") or entry.output_url or "")
    entry.created_at = str(job.get("created_at") or entry.created_at or "")
    entry.duration_seconds = int(job.get("duration_seconds") or entry.duration_seconds or 0)
    entry.resolution = str(job.get("resolution") or entry.resolution or "")
    entry.aspect_ratio = str(job.get("aspect_ratio") or entry.aspect_ratio or "")
    entry.credit_cost = int(
        job.get("reserved_credits") or job.get("credit_cost") or entry.credit_cost or 0
    )
    entry.error = str(job.get("error") or entry.error or "")
    entry.prompt = str(job.get("user_prompt") or job.get("prompt") or entry.prompt or "")
    entry.source_video_path = str(job.get("source_video_path") or entry.source_video_path or "")
    entry.style_reference_name = str(
        job.get("style_reference_name") or entry.style_reference_name or ""
    )
    if filepath:
        entry.filepath = filepath
    return entry


def _sync_video_history(scene) -> int:
    jobs = beta_api.list_video_jobs()
    for job in reversed(jobs):
        record_video_job(scene, job, source="SERVER")
    return len(jobs)


def _set_target_image(props, target: str, image: bpy.types.Image | None) -> None:
    attr = _TARGET_PROPERTIES.get(target)
    if not attr:
        raise ValueError("Unknown video image target")
    setattr(props, attr, image)


def _image_from_editor(context) -> bpy.types.Image | None:
    space = getattr(context, "space_data", None)
    if getattr(space, "type", None) == 'IMAGE_EDITOR' and getattr(space, "image", None):
        return _resolve_editor_image(context, space.image)

    window_manager = getattr(context, "window_manager", None)
    for window in getattr(window_manager, "windows", []) or []:
        for area in window.screen.areas:
            if area.type != 'IMAGE_EDITOR':
                continue
            image = getattr(area.spaces.active, "image", None)
            if image:
                return _resolve_editor_image(context, image)
    return None


def _latest_render_history_image(scene) -> bpy.types.Image | None:
    render_props = getattr(scene, "gemini_render", None) if scene else None
    history = getattr(render_props, "render_history", []) if render_props else []
    for index in range(len(history) - 1, -1, -1):
        image = _image_from_history_item(history[index])
        if image:
            return image
    return None


def _resolve_editor_image(context, image: bpy.types.Image | None) -> bpy.types.Image | None:
    if not image:
        return None
    if image.name in {'Render Result', 'Nano Banana Render'}:
        concrete = _latest_render_history_image(getattr(context, "scene", None))
        if concrete:
            return concrete
    return image


def _image_from_history_item(item) -> bpy.types.Image | None:
    image_name = str(getattr(item, "image_name", "") or "")
    if image_name and image_name in bpy.data.images:
        return bpy.data.images[image_name]

    filepath = bpy.path.abspath(str(getattr(item, "filepath", "") or ""))
    if filepath and os.path.isfile(filepath):
        return bpy.data.images.load(filepath, check_existing=True)
    return None


def _history_items(_operator, context):
    global _history_enum_cache
    items = []
    scene = getattr(context, "scene", None)
    render_props = getattr(scene, "gemini_render", None) if scene else None
    render_history = getattr(render_props, "render_history", []) if render_props else []
    for index in range(len(render_history) - 1, -1, -1):
        item = render_history[index]
        label = getattr(item, "image_name", "") or f"Render {index + 1}"
        items.append((f"RENDER:{index}", f"Render: {label}", getattr(item, "prompt", "")))

    editor_props = getattr(getattr(context, "window_manager", None), "nano_banana_editor", None)
    edit_history = getattr(editor_props, "edit_history", []) if editor_props else []
    for index in range(len(edit_history) - 1, -1, -1):
        item = edit_history[index]
        label = getattr(item, "image_name", "") or f"Edit {index + 1}"
        items.append((f"EDIT:{index}", f"Editor: {label}", getattr(item, "prompt", "")))

    if not items:
        items.append(("NONE", "No images in history", "Render or edit an image first"))
    _history_enum_cache = items
    return _history_enum_cache


class NanodeOTUseVideoImage(Operator):
    bl_idname = "nanode.video_use_image"
    bl_label = "Use Image"
    bl_description = "Use the image currently shown in an Image Editor"

    target: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        props = _video_props(context)
        image = _image_from_editor(context)
        if not props or not image:
            self.report({'ERROR'}, "No image is open in an Image Editor")
            return {'CANCELLED'}
        _set_target_image(props, self.target, image)
        if self.target == 'LAST' and not is_omni_model(props.model):
            props.task = 'first_last'
        elif self.target == 'FIRST' and props.task in {'auto', 'text_to_video'}:
            props.task = 'image_to_video'
        self.report({'INFO'}, f"Using {image.name}")
        return {'FINISHED'}


class NanodeOTPickHistoryImage(Operator):
    bl_idname = "nanode.video_pick_history_image"
    bl_label = "Choose History Image"
    bl_description = "Choose a Nano Banana render or Image Editor result"

    target: StringProperty(options={'HIDDEN'})
    history_item: EnumProperty(name="History", items=_history_items)

    def invoke(self, context, _event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        props = _video_props(context)
        if not props or self.history_item == "NONE":
            self.report({'ERROR'}, "No history image is available")
            return {'CANCELLED'}

        source, raw_index = self.history_item.split(":", 1)
        index = int(raw_index)
        if source == "RENDER":
            collection = context.scene.gemini_render.render_history
        else:
            editor_props = getattr(context.window_manager, "nano_banana_editor", None)
            collection = getattr(editor_props, "edit_history", []) if editor_props else []

        if index < 0 or index >= len(collection):
            self.report({'ERROR'}, "History item is no longer available")
            return {'CANCELLED'}
        image = _image_from_history_item(collection[index])
        if not image:
            self.report({'ERROR'}, "History image could not be loaded")
            return {'CANCELLED'}

        _set_target_image(props, self.target, image)
        if self.target == 'LAST' and not is_omni_model(props.model):
            props.task = 'first_last'
        elif self.target == 'FIRST' and props.task in {'auto', 'text_to_video'}:
            props.task = 'image_to_video'
        self.report({'INFO'}, f"Using {image.name}")
        return {'FINISHED'}


class NanodeOTUseRenderHistoryImage(Operator):
    bl_idname = "nanode.video_use_render_history"
    bl_label = "Use Render for Video"
    bl_description = "Use this exact render history image as a video frame"

    target: StringProperty(options={'HIDDEN'})
    history_index: IntProperty(options={'HIDDEN'})

    def execute(self, context):
        props = _video_props(context)
        history = getattr(getattr(context.scene, "gemini_render", None), "render_history", [])
        if not props or self.history_index < 0 or self.history_index >= len(history):
            self.report({'ERROR'}, "Render history item is no longer available")
            return {'CANCELLED'}
        image = _image_from_history_item(history[self.history_index])
        if not image:
            self.report({'ERROR'}, "Render history image could not be loaded")
            return {'CANCELLED'}

        _set_target_image(props, self.target, image)
        if self.target == 'LAST' and not is_omni_model(props.model):
            props.task = 'first_last'
        elif self.target == 'FIRST' and props.task in {'auto', 'text_to_video'}:
            props.task = 'image_to_video'
        self.report({'INFO'}, f"Using exact frame {image.name}")
        return {'FINISHED'}


class NanodeOTLoadVideoImage(Operator, ImportHelper):
    bl_idname = "nanode.video_load_image"
    bl_label = "Load Video Reference"
    bl_description = "Load an image from disk"

    target: StringProperty(options={'HIDDEN'})
    filter_glob: StringProperty(default="*.png;*.jpg;*.jpeg;*.webp;*.tif;*.tiff;*.exr", options={'HIDDEN'})

    def execute(self, context):
        props = _video_props(context)
        if not props or not os.path.isfile(self.filepath):
            self.report({'ERROR'}, "Image file not found")
            return {'CANCELLED'}
        try:
            image = bpy.data.images.load(self.filepath, check_existing=True)
            _set_target_image(props, self.target, image)
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, f"Could not load image: {exc}")
            return {'CANCELLED'}


class NanodeOTLoadSourceVideo(Operator, ImportHelper):
    bl_idname = "nanode.video_load_source"
    bl_label = "Load Source Video"
    bl_description = "Choose a video for Omni Edit Video"

    filter_glob: StringProperty(default="*.mp4;*.mov;*.mkv;*.webm", options={'HIDDEN'})

    def execute(self, context):
        props = _video_props(context)
        if not props or not os.path.isfile(self.filepath):
            self.report({'ERROR'}, "Video file not found")
            return {'CANCELLED'}
        try:
            _assign_source_video(props, self.filepath)
        except Exception as exc:
            self.report({'ERROR'}, f"Could not read video duration: {exc}")
            return {'CANCELLED'}
        return {'FINISHED'}


class NanodeOTUseLastVideo(Operator):
    bl_idname = "nanode.video_use_last_result"
    bl_label = "Use Last Generated"
    bl_description = "Use the latest generated Nanode video as the Omni edit source"

    def execute(self, context):
        props = _video_props(context)
        if not props or not props.last_video_path or not os.path.isfile(bpy.path.abspath(props.last_video_path)):
            self.report({'ERROR'}, "No generated video is available")
            return {'CANCELLED'}
        try:
            _assign_source_video(props, props.last_video_path)
        except Exception as exc:
            self.report({'ERROR'}, f"Could not read video duration: {exc}")
            return {'CANCELLED'}
        return {'FINISHED'}


def _movie_strip_path(strip) -> str:
    filepath = str(getattr(strip, "filepath", "") or "")
    if not filepath:
        elements = getattr(strip, "elements", None)
        if elements and len(elements):
            filename = str(getattr(elements[0], "filename", "") or "")
            directory = str(getattr(strip, "directory", "") or "")
            filepath = os.path.join(directory, filename) if filename else ""
    return bpy.path.abspath(filepath) if filepath else ""


def _selected_movie_strip(context):
    scene = getattr(context, "scene", None)
    sequence_editor = getattr(scene, "sequence_editor", None) if scene else None
    if not sequence_editor:
        return None

    active = getattr(sequence_editor, "active_strip", None)
    if active and getattr(active, "type", "") == 'MOVIE':
        return active
    return next(
        (
            strip
            for strip in _all_sequence_strips(sequence_editor)
            if getattr(strip, "type", "") == 'MOVIE' and getattr(strip, "select", False)
        ),
        None,
    )


class NanodeOTUseSelectedVideoStrip(Operator):
    bl_idname = "nanode.video_use_selected_strip"
    bl_label = "Use Selected Clip"
    bl_description = "Use the selected Movie Strip as the Omni edit source"

    def execute(self, context):
        props = _video_props(context)
        strip = _selected_movie_strip(context)
        filepath = _movie_strip_path(strip) if strip else ""
        if not props or not filepath or not os.path.isfile(filepath):
            self.report({'ERROR'}, "Select a Movie Strip with an available source file")
            return {'CANCELLED'}
        try:
            _assign_source_video(props, filepath)
        except Exception as exc:
            self.report({'ERROR'}, f"Could not read video duration: {exc}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Using {strip.name}")
        return {'FINISHED'}


def _visible_sequence_strip_at_frame(scene, frame: int):
    sequence_editor = getattr(scene, "sequence_editor", None)
    if not sequence_editor:
        return None
    return next(
        (
            strip
            for strip in reversed(_all_sequence_strips(sequence_editor))
            if getattr(strip, "type", "") != 'SOUND'
            and not getattr(strip, "mute", False)
            and int(getattr(strip, "frame_final_start", 0)) <= frame
            < int(getattr(strip, "frame_final_end", 0))
        ),
        None,
    )


def _capture_sequencer_playhead_frame(scene) -> bpy.types.Image:
    frame = int(scene.frame_current)
    if not _visible_sequence_strip_at_frame(scene, frame):
        raise RuntimeError(f"No visible video frame at timeline frame {frame}")

    from . import render_engine
    from . import texture_pipeline

    render = scene.render
    render_snapshot = texture_pipeline._store_render_settings(scene)
    output_snapshot = render_engine._store_omni_output_settings(scene)
    use_sequencer = render.use_sequencer
    use_file_extension = render.use_file_extension
    use_compositing = render.use_compositing
    temp_dir = tempfile.mkdtemp(prefix="nanode_video_continue_")
    output_path = os.path.join(temp_dir, f"timeline_frame_{frame:06d}.png")
    image = None
    try:
        render.engine = texture_pipeline._eevee_name()
        render.use_sequencer = True
        render.use_file_extension = True
        render.use_compositing = False
        render.filepath = output_path
        render.resolution_percentage = 100
        scene.use_nodes = False
        settings = render.image_settings
        if hasattr(settings, "media_type"):
            settings.media_type = 'IMAGE'
        settings.file_format = 'PNG'
        settings.color_mode = 'RGB'
        settings.color_depth = '8'
        bpy.ops.render.render(write_still=True, scene=scene.name)
        if not os.path.isfile(output_path) or os.path.getsize(output_path) < 128:
            raise RuntimeError("Blender did not render the timeline frame")
        image = bpy.data.images.load(output_path, check_existing=False)
        image.name = f"Nanode_Continue_{scene.name}_{frame:06d}_{int(time.time() * 1000)}"
        image.pack()
        return image
    except Exception:
        if image and image.name in bpy.data.images:
            bpy.data.images.remove(image)
        raise
    finally:
        render_engine._restore_omni_output_settings(scene, output_snapshot)
        texture_pipeline._restore_render_settings(scene, render_snapshot)
        render.use_sequencer = use_sequencer
        render.use_file_extension = use_file_extension
        render.use_compositing = use_compositing
        shutil.rmtree(temp_dir, ignore_errors=True)


class NanodeOTContinueFromPlayhead(Operator):
    bl_idname = "nanode.video_continue_from_playhead"
    bl_label = "Continue from Playhead"
    bl_description = "Use the currently displayed Sequencer frame as the first frame for a new video"

    def execute(self, context):
        props = _video_props(context)
        if not props:
            return {'CANCELLED'}
        try:
            image = _capture_sequencer_playhead_frame(context.scene)
            props.input_image = image
            props.task = 'image_to_video'
            props.continuation_source_frame = int(context.scene.frame_current)
            props.aspect_ratio = '9:16' if image.size[1] > image.size[0] else '16:9'
            props.status = f"Continuation frame ready: {context.scene.frame_current}"
            self.report({'INFO'}, f"Using timeline frame {context.scene.frame_current} with {props.model}")
            return {'FINISHED'}
        except Exception as exc:
            props.status = f"Could not capture timeline frame: {exc}"
            self.report({'ERROR'}, props.status)
            return {'CANCELLED'}


class NanodeOTClearVideoImage(Operator):
    bl_idname = "nanode.video_clear_image"
    bl_label = "Clear Image"
    bl_description = "Remove the selected video input image"

    target: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        props = _video_props(context)
        if not props:
            return {'CANCELLED'}
        _set_target_image(props, self.target, None)
        return {'FINISHED'}


def _export_image(image: bpy.types.Image, temp_dir: str, filename: str) -> str:
    path = os.path.join(temp_dir, filename)
    try:
        from PIL import Image as PILImage
        import numpy as np

        width, height = image.size
        if width <= 0 or height <= 0:
            raise RuntimeError("Image has no pixel data")
        pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape((height, width, image.channels))
        pixels = np.flip(pixels, axis=0)
        pixels = np.clip(pixels, 0.0, 1.0)
        data = (pixels * 255.0 + 0.5).astype(np.uint8)
        if image.channels >= 4:
            output = PILImage.fromarray(data[:, :, :4], "RGBA")
        else:
            rgb = data[:, :, :3]
            if rgb.shape[2] == 1:
                rgb = np.repeat(rgb, 3, axis=2)
            elif rgb.shape[2] == 2:
                rgb = np.concatenate((rgb, rgb[:, :, :1]), axis=2)
            output = PILImage.fromarray(rgb, "RGB")
        output.save(path, "PNG")
    except Exception:
        scene = bpy.context.scene
        settings = scene.render.image_settings
        original = {
            "media_type": getattr(settings, "media_type", None),
            "file_format": settings.file_format,
            "color_mode": settings.color_mode,
            "color_depth": settings.color_depth,
        }
        try:
            if hasattr(settings, "media_type"):
                settings.media_type = 'IMAGE'
            settings.file_format = 'PNG'
            settings.color_mode = 'RGBA' if image.channels >= 4 else 'RGB'
            settings.color_depth = '8'
            image.save_render(path, scene=scene)
        finally:
            if original["media_type"] is not None:
                settings.media_type = original["media_type"]
            settings.file_format = original["file_format"]
            settings.color_mode = original["color_mode"]
            settings.color_depth = original["color_depth"]

    if not os.path.isfile(path) or os.path.getsize(path) < 128:
        raise RuntimeError(f"Could not export {image.name}")
    with open(path, "rb") as exported:
        gemini_api._image_mime_type(exported.read(16))
    return path


def _save_direct_video(video_bytes: bytes) -> str:
    if len(video_bytes) < 1024:
        raise RuntimeError("Google Omni returned an empty video")
    output_dir = os.path.join(tempfile.gettempdir(), "nanode_blender", "videos")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"nanode_omni_personal_{int(time.time())}.mp4")
    with open(output_path, "wb") as output:
        output.write(video_bytes)
    return output_path


def _effective_duration(props) -> int:
    if is_omni_model(props.model):
        return int(props.duration)
    if props.resolution in {'1080p', '4k'} or props.task in {'first_last', 'reference_to_video'}:
        return 8
    return min(8, int(props.duration))


def _build_omni_media_prompt(prompt: str, task: str, reference_count: int = 0) -> str:
    prompt = prompt.strip()
    if task == 'image_to_video':
        return (
            f"[# Sources <FIRST_FRAME>@Image1]\n<FIRST_FRAME> {prompt}\n"
            "Use Image1 as the exact starting frame. Preserve its subjects, composition, materials, "
            "and visual identity while adding only the requested motion."
        )
    if task == 'reference_to_video' and reference_count:
        declarations = " ".join(
            f"<IMAGE_REF_{index}>@Image{index + 1}" for index in range(reference_count)
        )
        references = ", ".join(f"<IMAGE_REF_{index}>" for index in range(reference_count))
        return (
            f"[# References {declarations}]\n{prompt}\n"
            f"Use {references} as exact visual and subject references. Preserve identity, materials, "
            "palette, proportions, and distinctive details consistently throughout the video. "
            "The references are not literal initial frames."
        )
    return prompt


def _build_video_edit_prompt(prompt: str, has_style_reference: bool = False) -> str:
    base_prompt = (
        "Edit the uploaded source video according to the user request. Use the source video as "
        "the basis for duration, timing, camera path, subject movement, geometry, and framing. "
        "Preserve those properties unless the user explicitly requests a change. Treat every "
        "foreground character and primary subject as identity-locked: preserve the exact face, "
        "body proportions, hairstyle, clothing, footwear, accessories, held objects, colors, and "
        "silhouette. Do not invent capes, coats, armor, jewelry, bags, hats, or props. Background "
        "detail may be enriched only when it does not touch, cover, or alter a foreground subject. "
        f"User edit request: {prompt.strip()}"
    )
    if not has_style_reference:
        return base_prompt
    return gemini_api.append_style_reference_policy(
        f"[# References <IMAGE_REF_0>@Image1]\n{base_prompt}",
        reference_label="Image1",
        source_label="the uploaded source video",
        preserve_fields=[
            "duration",
            "timing",
            "camera_path",
            "subject_movement",
            "subject_identity",
            "face",
            "body_proportions",
            "wardrobe",
            "accessories",
            "geometry",
            "composition",
            "framing",
        ],
    )


def _model_validation_error(props) -> str:
    if is_omni_model(props.model):
        if props.resolution != '720p':
            return "Gemini Omni Flash supports 720p only"
        if props.task == 'first_last':
            return "Use Image to Video or Reference Images with Omni"
        if props.task == 'edit' and not os.path.isfile(bpy.path.abspath(props.source_video_path)):
            return "Select a source video for Omni Edit Video"
        if props.task == 'edit' and props.use_style_reference and not props.style_reference_image:
            return "Select a style reference image or disable Style Reference"
        if props.task == 'image_to_video' and not props.input_image:
            return "Select a first frame"
        if props.task == 'reference_to_video' and not any(
            (props.reference_image, props.reference_image_2, props.reference_image_3)
        ):
            return "Select at least one reference image"
        return ""

    if props.task in {'auto', 'edit'}:
        return "This mode is available with Gemini Omni Flash"
    if props.model == 'veo-3.1-lite-generate-preview':
        if props.resolution == '4k':
            return "Veo Lite does not support 4K"
        if props.task in {'first_last', 'reference_to_video'}:
            return "First/last frames and reference images require Veo Fast or Standard"
    if props.task == 'reference_to_video' and not any(
        (props.reference_image, props.reference_image_2, props.reference_image_3)
    ):
        return "Select at least one reference image"
    if props.task in {'image_to_video', 'first_last'} and not props.input_image:
        return "Select a first frame"
    if props.task == 'first_last' and not props.last_frame_image:
        return "Select a last frame"
    return ""


class NanodeOTSubmitDirectorJob(Operator):
    bl_idname = "nanode.video_director_submit"
    bl_label = "Generate Video"
    bl_description = "Queue a Nanode video and load the result into this scene"

    def execute(self, context):
        props = _video_props(context)
        if not props:
            self.report({'ERROR'}, "Video Director is unavailable")
            return {'CANCELLED'}
        token = _get_configured_token(context)
        is_nanode = auth_utils.is_nanode_token(token)
        is_personal = auth_utils.is_google_api_key(token)
        if not is_nanode and not is_personal:
            props.status = "Nanode Login or Personal Google API Key required"
            self.report({'ERROR'}, props.status)
            return {'CANCELLED'}
        if is_personal and not is_omni_model(props.model):
            props.status = "Personal Google API mode supports Gemini Omni in Video Director"
            self.report({'ERROR'}, props.status)
            return {'CANCELLED'}

        user_prompt = props.prompt.strip()
        prompt = user_prompt
        if len(prompt) < 3:
            props.status = "Enter a video prompt"
            self.report({'ERROR'}, props.status)
            return {'CANCELLED'}

        validation_error = _model_validation_error(props)
        if validation_error:
            props.status = validation_error
            self.report({'ERROR'}, validation_error)
            return {'CANCELLED'}

        duration = _effective_duration(props)
        match_source_duration = bool(
            is_omni_model(props.model)
            and props.task == 'edit'
            and props.match_source_duration
        )
        cost = get_video_cost(props.model, props.task, props.resolution, duration)
        if cost is None:
            props.status = "Selected model does not support this resolution"
            self.report({'ERROR'}, props.status)
            return {'CANCELLED'}

        if is_nanode:
            try:
                account = beta_api.validate_nanode_token()
                if "balance" in account and hasattr(context.scene, "gemini_render"):
                    context.scene.gemini_render.beta_balance = int(account.get("balance") or 0)
            except beta_api.BetaAPIError as exc:
                props.status = (
                    "Nanode login expired. Log in with Google again."
                    if beta_api.is_invalid_token_error(exc)
                    else f"Nanode server check failed: {exc.message}"
                )
                self.report({'ERROR'}, props.status)
                return {'CANCELLED'}

        temp_dir = tempfile.mkdtemp(prefix="nanode_video_director_")
        try:
            first_path = None
            last_path = None
            reference_paths = []
            video_path = None
            api_task = props.task

            if props.task in {'image_to_video', 'first_last'}:
                first_path = _export_image(props.input_image, temp_dir, "first.png")
            if props.task == 'first_last':
                last_path = _export_image(props.last_frame_image, temp_dir, "last.png")
                api_task = 'image_to_video'
            if props.task == 'reference_to_video':
                for index, image in enumerate(
                    (props.reference_image, props.reference_image_2, props.reference_image_3), start=1
                ):
                    if image:
                        reference_paths.append(_export_image(image, temp_dir, f"reference_{index}.png"))
            if is_omni_model(props.model) and props.task in {'image_to_video', 'reference_to_video'}:
                prompt = _build_omni_media_prompt(prompt, props.task, len(reference_paths))
            if is_omni_model(props.model) and props.task == 'edit':
                video_path = bpy.path.abspath(props.source_video_path)
                if props.use_style_reference and props.style_reference_image:
                    reference_paths.append(
                        _export_image(props.style_reference_image, temp_dir, "style_reference.png")
                    )
                prompt = _build_video_edit_prompt(prompt, bool(reference_paths))

            if is_personal:
                props.status = "Generating with Personal Google API..."
                video_bytes, interaction_id = gemini_api.generate_omni_video_direct(
                    api_key=token,
                    prompt=prompt,
                    task=api_task,
                    aspect_ratio=props.aspect_ratio,
                    duration_seconds=duration,
                    input_image_path=first_path,
                    reference_image_paths=reference_paths,
                    video_path=video_path,
                    match_source_duration=match_source_duration,
                )
                output_path = _save_direct_video(video_bytes)
                local_id = int(time.time())
                local_job = {
                    "entry_id": f"personal:{interaction_id or local_id}",
                    "model": props.model,
                    "task": api_task,
                    "status": "succeeded",
                    "duration_seconds": duration,
                    "resolution": props.resolution,
                    "aspect_ratio": props.aspect_ratio,
                    "user_prompt": user_prompt,
                    "source_video_path": video_path or "",
                    "style_reference_name": (
                        props.style_reference_image.name
                        if props.use_style_reference and props.style_reference_image
                        else ""
                    ),
                }
                record_video_job(context.scene, local_job, source="DIRECTOR", filepath=output_path)
                load_video_path_to_sequencer(output_path, local_id, "Omni Personal", context.scene.name)
                props.last_job_id = 0
                props.loaded_job_id = 0
                props.output_url = ""
                props.status = "Video ready in Sequencer"
                self.report({'INFO'}, props.status)
                return {'FINISHED'}

            props.status = "Queueing video job..."
            response = beta_api.create_video_job(
                prompt=prompt,
                model=props.model,
                task=api_task,
                duration_seconds=duration,
                resolution=props.resolution,
                aspect_ratio=props.aspect_ratio,
                input_image_path=first_path,
                last_frame_image_path=last_path,
                reference_image_paths=reference_paths,
                video_path=video_path,
                request_id=uuid.uuid4().hex,
                match_source_duration=match_source_duration,
            )
            job = response.get("job", response)
            job["user_prompt"] = user_prompt
            job["source_video_path"] = video_path or ""
            job["style_reference_name"] = (
                props.style_reference_image.name
                if props.use_style_reference and props.style_reference_image
                else ""
            )
            props.last_job_id = int(job.get("id") or 0)
            props.loaded_job_id = 0
            props.output_url = job.get("output_url") or ""
            props.status = f"Queued ({job.get('credit_cost', cost)} credits)"
            record_video_job(context.scene, job, source="DIRECTOR")
            schedule_video_director_poll(context.scene.name, props.last_job_id)
            self.report({'INFO'}, props.status)
            return {'FINISHED'}
        except beta_api.BetaAPIError as exc:
            props.status = (
                "Nanode login expired. Log in with Google again."
                if beta_api.is_invalid_token_error(exc)
                else f"Video job failed: {exc.message}"
            )
            self.report({'ERROR'}, props.status)
            return {'CANCELLED'}
        except Exception as exc:
            props.status = f"Video job failed: {exc}"
            self.report({'ERROR'}, props.status)
            return {'CANCELLED'}
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class NanodeOTSubmitVideoEdit(Operator):
    bl_idname = "nanode.video_editor_submit"
    bl_label = "Edit Video"
    bl_description = "Edit the source clip with Gemini Omni and load the result into the Sequencer"

    def execute(self, context):
        props = _video_props(context)
        if not props:
            self.report({'ERROR'}, "AI Video Editor is unavailable")
            return {'CANCELLED'}
        duration_error = _edit_duration_validation_error(props)
        if duration_error:
            props.status = duration_error
            self.report({'ERROR'}, duration_error)
            return {'CANCELLED'}
        try:
            duration = _effective_edit_duration(props)
        except Exception as exc:
            props.status = f"Could not detect source duration: {exc}"
            self.report({'ERROR'}, props.status)
            return {'CANCELLED'}

        props.model = 'gemini-omni-flash-preview'
        props.task = 'edit'
        props.resolution = '720p'
        props.duration = str(duration)
        props.match_source_duration = props.edit_duration == 'AUTO'
        props.aspect_ratio = props.edit_aspect_ratio
        return NanodeOTSubmitDirectorJob.execute(self, context)


class NanodeOTRefreshDirectorJob(Operator):
    bl_idname = "nanode.video_director_refresh"
    bl_label = "Refresh Job"
    bl_description = "Refresh the latest video job"

    def execute(self, context):
        props = _video_props(context)
        if not props or props.last_job_id <= 0:
            self.report({'WARNING'}, "No video job yet")
            return {'CANCELLED'}
        try:
            response = beta_api.get_video_job(props.last_job_id)
            _apply_job_response(context.scene.name, props.last_job_id, response)
            self.report({'INFO'}, props.status)
            return {'FINISHED'}
        except beta_api.BetaAPIError as exc:
            props.status = (
                "Nanode login expired. Log in with Google again."
                if beta_api.is_invalid_token_error(exc)
                else f"Refresh failed: {exc.message}"
            )
            self.report({'ERROR'}, props.status)
            return {'CANCELLED'}


class NanodeOTRefreshVideoHistory(Operator):
    bl_idname = "nanode.video_history_refresh"
    bl_label = "Refresh Video History"
    bl_description = "Sync video jobs from the Nanode account"

    def execute(self, context):
        if not _get_nanode_token(context):
            self.report({'ERROR'}, "Nanode login required")
            return {'CANCELLED'}
        try:
            count = _sync_video_history(context.scene)
            self.report({'INFO'}, f"Synced {count} video jobs")
            return {'FINISHED'}
        except beta_api.BetaAPIError as exc:
            self.report({'ERROR'}, f"Video history failed: {exc.message}")
            return {'CANCELLED'}


class NanodeOTPlayVideoHistory(Operator):
    bl_idname = "nanode.video_history_play"
    bl_label = "Open Video Preview"
    bl_description = "Load this video in the current scene and open Blender Preview"

    history_index: IntProperty(options={'HIDDEN'})

    def execute(self, context):
        props = _video_props(context)
        if not props or self.history_index < 0 or self.history_index >= len(props.video_history):
            self.report({'ERROR'}, "Video history item is no longer available")
            return {'CANCELLED'}
        item = props.video_history[self.history_index]
        try:
            path = bpy.path.abspath(item.filepath) if item.filepath else ""
            if not path or not os.path.isfile(path):
                if not item.output_url:
                    raise RuntimeError("Video result is not available")
                path = beta_api.download_video_result(item.output_url, item.job_id)
                item.filepath = path
            load_video_path_to_sequencer(
                path,
                item.job_id,
                "Nanode History",
                context.scene.name,
                open_editor=True,
            )
            self.report({'INFO'}, f"Loaded {os.path.basename(path)}")
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, f"Could not load video: {exc}")
            return {'CANCELLED'}


class NanodeOTRemoveVideoHistory(Operator):
    bl_idname = "nanode.video_history_remove"
    bl_label = "Remove from Video History"
    bl_description = "Remove this local history entry without deleting the server job"

    history_index: IntProperty(options={'HIDDEN'})

    def execute(self, context):
        props = _video_props(context)
        if not props or self.history_index < 0 or self.history_index >= len(props.video_history):
            return {'CANCELLED'}
        props.video_history.remove(self.history_index)
        return {'FINISHED'}


class NanodeOTReuseOmniHistory(Operator):
    bl_idname = "nanode.video_history_reuse_omni"
    bl_label = "Reuse Source & Prompt"
    bl_description = "Restore this motion guide and prompt in Omni Engine without starting a paid generation"

    history_index: IntProperty(options={'HIDDEN'})

    def execute(self, context):
        props = _video_props(context)
        if not props or self.history_index < 0 or self.history_index >= len(props.video_history):
            self.report({'ERROR'}, "Video history item is no longer available")
            return {'CANCELLED'}

        item = props.video_history[self.history_index]
        source_path = bpy.path.abspath(item.source_video_path) if item.source_video_path else ""
        if not source_path or not os.path.isfile(source_path):
            self.report({'ERROR'}, "The original Omni motion guide is no longer available")
            return {'CANCELLED'}

        render_props = getattr(context.scene, "gemini_render", None)
        if not render_props:
            self.report({'ERROR'}, "Omni Engine settings are unavailable")
            return {'CANCELLED'}

        context.scene.render.engine = 'NANODE_OMNI'
        render_props.omni_input_mode = 'VIDEO_EDIT'
        render_props.omni_source_video_override = source_path
        if item.prompt:
            render_props.prompt = item.prompt
        duration = str(item.duration_seconds or 10)
        valid_durations = {entry[0] for entry in OMNI_DURATION_ITEMS}
        render_props.omni_duration = duration if duration in valid_durations else '10'
        if item.aspect_ratio in {'16:9', '9:16'}:
            render_props.omni_aspect_ratio = item.aspect_ratio

        style_image = bpy.data.images.get(item.style_reference_name) if item.style_reference_name else None
        render_props.use_style_reference = style_image is not None
        if style_image:
            render_props.style_reference_image = style_image
        render_props.omni_status = "Motion guide and prompt restored; edit the prompt, then render"
        self.report({'INFO'}, "Omni source restored; generation has not started")
        return {'FINISHED'}


class NanodeOTClearOmniReuseSource(Operator):
    bl_idname = "nanode.omni_clear_reuse_source"
    bl_label = "Use Scene Capture"
    bl_description = "Stop reusing the history motion guide and capture the current Blender scene"

    def execute(self, context):
        props = getattr(context.scene, "gemini_render", None)
        if not props:
            return {'CANCELLED'}
        props.omni_source_video_override = ""
        props.omni_status = "Current scene will be captured on the next render"
        return {'FINISHED'}


def _editable_strip_collection(sequence_editor):
    collection = getattr(sequence_editor, "sequences", None)
    if collection is None:
        collection = getattr(sequence_editor, "strips", None)
    if collection is None:
        raise RuntimeError("Sequence strip collection is unavailable")
    return collection


def _all_sequence_strips(sequence_editor) -> list:
    collection = getattr(sequence_editor, "sequences_all", None)
    if collection is None:
        collection = getattr(sequence_editor, "strips_all", None)
    if collection is None:
        collection = _editable_strip_collection(sequence_editor)
    return list(collection)


def _next_sequence_channel(scene, frame_start: int, frame_end: int, required_channels: int = 1) -> int:
    sequence_editor = scene.sequence_editor
    if not sequence_editor:
        return 1
    for channel in range(1, 65 - max(1, required_channels)):
        occupied = False
        for candidate_channel in range(channel, channel + required_channels):
            for strip in _all_sequence_strips(sequence_editor):
                if strip.channel != candidate_channel:
                    continue
                if strip.frame_final_start < frame_end and strip.frame_final_end > frame_start:
                    occupied = True
                    break
            if occupied:
                break
        if not occupied:
            return channel
    return 63


def load_video_result_to_sequencer(
    output_url: str,
    job_id: int,
    label: str = "Nanode Video",
    scene_name: str = "",
) -> str:
    video_path = beta_api.download_video_result(output_url, job_id)
    return load_video_path_to_sequencer(video_path, job_id, label, scene_name)


def _dedicated_preview_window():
    window_manager = getattr(bpy.context, "window_manager", None)
    for window in getattr(window_manager, "windows", []) or []:
        screen = getattr(window, "screen", None)
        if screen and bool(screen.get(_PREVIEW_SCREEN_KEY, False)):
            return window
    return None


def _render_preview_area():
    window_manager = getattr(bpy.context, "window_manager", None)
    current_window = getattr(bpy.context, "window", None)
    exact_candidates = []
    temporary_candidates = []
    detached_candidates = []
    for window in getattr(window_manager, "windows", []) or []:
        for area in window.screen.areas:
            if area.type != 'IMAGE_EDITOR':
                continue
            space = area.spaces.active
            image_name = str(getattr(getattr(space, "image", None), "name", "") or "")
            candidate = (
                window is not current_window,
                area.width * area.height,
                window,
                area,
            )
            if image_name in {'Render Result', 'Nano Banana Render'}:
                exact_candidates.append(candidate)
            elif bool(getattr(window.screen, "is_temporary", False)):
                temporary_candidates.append(candidate)
            elif window is not current_window:
                detached_candidates.append(candidate)
    candidates = exact_candidates or temporary_candidates or detached_candidates
    if not candidates:
        return None
    _, _, window, area = max(candidates, key=lambda item: (item[0], item[1]))
    return window, area


def _create_preview_window():
    if bpy.app.background:
        return None
    window_manager = getattr(bpy.context, "window_manager", None)
    windows = list(getattr(window_manager, "windows", []) or [])
    source_window = getattr(bpy.context, "window", None) or (windows[0] if windows else None)
    if not source_window:
        return None
    source_area = next(
        (area for area in source_window.screen.areas if area.type == 'VIEW_3D'),
        source_window.screen.areas[0] if source_window.screen.areas else None,
    )
    if not source_area:
        return None

    existing = {window.as_pointer() for window in windows}
    region = next((item for item in source_area.regions if item.type == 'WINDOW'), None)
    override = {"window": source_window, "area": source_area}
    if region:
        override["region"] = region
    with bpy.context.temp_override(**override):
        result = bpy.ops.screen.area_dupli()
    if 'FINISHED' not in result:
        return None
    return next(
        (
            window
            for window in getattr(window_manager, "windows", []) or []
            if window.as_pointer() not in existing
        ),
        None,
    )


def _activate_sequence_strip(scene, strip_name: str = ""):
    sequence_editor = getattr(scene, "sequence_editor", None)
    if not sequence_editor:
        return None
    strips = _all_sequence_strips(sequence_editor)
    target = next((strip for strip in strips if strip.name == strip_name), None) if strip_name else None
    if target is None:
        target = next((strip for strip in reversed(strips) if strip.type == 'MOVIE'), None)
    if target is None:
        return None
    for strip in strips:
        strip.select = strip == target
    if hasattr(sequence_editor, "active_strip"):
        sequence_editor.active_strip = target
    scene.frame_set(max(int(scene.frame_start), int(target.frame_final_start)))
    return target


def _focus_sequence_preview(window, area, scene, strip_name: str = "") -> None:
    window.scene = scene
    if scene.view_layers and hasattr(window, "view_layer"):
        window.view_layer = scene.view_layers[0]
    target = _activate_sequence_strip(scene, strip_name)

    if area.type != 'SEQUENCE_EDITOR':
        area.type = 'SEQUENCE_EDITOR'
    space = area.spaces.active
    space.view_type = 'SEQUENCER_PREVIEW'
    space.display_mode = 'IMAGE'
    space.display_channel = 0
    space.preview_channels = 'COLOR_ALPHA'
    space.use_zoom_to_fit = True
    if hasattr(space, "show_region_ui"):
        space.show_region_ui = False

    for region in area.regions:
        if region.type not in {'WINDOW', 'PREVIEW'}:
            continue
        override = {"window": window, "area": area, "region": region, "scene": scene}
        try:
            with bpy.context.temp_override(**override):
                bpy.ops.sequencer.view_all()
        except Exception:
            pass
        try:
            with bpy.context.temp_override(**override):
                bpy.ops.sequencer.view_all_preview()
        except Exception:
            pass
    area.tag_redraw()
    print(
        f"[NANODE VIDEO] Preview focused: scene={scene.name}, "
        f"strip={getattr(target, 'name', 'none')}, frame={scene.frame_current}"
    )


def _configure_preview_area(window, area, scene, strip_name: str = "") -> None:
    screen = window.screen
    screen[_PREVIEW_SCREEN_KEY] = True
    area.type = 'SEQUENCE_EDITOR'
    space = area.spaces.active
    if hasattr(space, "view_type"):
        space.view_type = 'SEQUENCER_PREVIEW'
    if hasattr(space, "show_region_ui"):
        space.show_region_ui = False

    _focus_sequence_preview(window, area, scene, strip_name)

    if not bpy.app.background:
        window_pointer = window.as_pointer()
        area_pointer = area.as_pointer()
        scene_name = scene.name

        def _delayed_focus():
            delayed_scene = bpy.data.scenes.get(scene_name)
            for candidate_window in bpy.context.window_manager.windows:
                if candidate_window.as_pointer() != window_pointer:
                    continue
                for candidate_area in candidate_window.screen.areas:
                    if candidate_area.as_pointer() == area_pointer and delayed_scene:
                        _focus_sequence_preview(
                            candidate_window,
                            candidate_area,
                            delayed_scene,
                            strip_name,
                        )
                        return None
            return None

        bpy.app.timers.register(_delayed_focus, first_interval=0.25)
    area.tag_redraw()
    print("[NANODE VIDEO] Render Preview switched to Sequencer & Preview")


def _configure_preview_window(window, scene, strip_name: str = "") -> None:
    screen = window.screen
    if not screen.areas:
        return
    area = next(
        (item for item in screen.areas if item.type == 'SEQUENCE_EDITOR'),
        max(screen.areas, key=lambda item: item.width * item.height),
    )
    _configure_preview_area(window, area, scene, strip_name)


def _show_video_preview(scene_name: str, strip_name: str = "") -> None:
    scene = bpy.data.scenes.get(scene_name)
    if not scene or bpy.app.background:
        return
    render_preview = _render_preview_area()
    if render_preview:
        window, area = render_preview
        _configure_preview_area(window, area, scene, strip_name)
        return
    window = _dedicated_preview_window() or _create_preview_window()
    if not window:
        raise RuntimeError("Could not find Render Preview or create a Video Editor window")
    _configure_preview_window(window, scene, strip_name)


def _schedule_video_preview(scene_name: str, strip_name: str = "") -> None:
    def _open_preview():
        try:
            _show_video_preview(scene_name, strip_name)
        except Exception as exc:
            print(f"[NANODE VIDEO] Could not open video preview: {exc}")
        return None

    bpy.app.timers.register(_open_preview, first_interval=0.1)


def _video_editing_workspace():
    preferred_names = ("Video Editing", "Nanode AI Video")
    for name in preferred_names:
        workspace = bpy.data.workspaces.get(name)
        if workspace:
            return workspace
    return next(
        (
            workspace
            for workspace in bpy.data.workspaces
            if "video" in workspace.name.lower()
            and any(
                area.type == 'SEQUENCE_EDITOR'
                for screen in workspace.screens
                for area in screen.areas
            )
        ),
        None,
    )


def _focus_video_editor(window, scene, strip_name: str = "") -> None:
    workspace = _video_editing_workspace()
    if workspace and window.workspace != workspace:
        window.workspace = workspace
    window.scene = scene
    if scene.view_layers and hasattr(window, "view_layer"):
        window.view_layer = scene.view_layers[0]
    target = _activate_sequence_strip(scene, strip_name)

    sequence_areas = [area for area in window.screen.areas if area.type == 'SEQUENCE_EDITOR']
    if sequence_areas:
        timeline_area = next(
            (
                area
                for area in sequence_areas
                if getattr(area.spaces.active, "view_type", "") == 'SEQUENCER'
            ),
            min(sequence_areas, key=lambda area: area.height),
        )
        if len(sequence_areas) == 1:
            timeline_area.spaces.active.view_type = 'SEQUENCER_PREVIEW'
    else:
        candidates = [
            area
            for area in window.screen.areas
            if area.type in {'VIEW_3D', 'IMAGE_EDITOR', 'NODE_EDITOR'}
        ]
        if not candidates:
            candidates = [
                area
                for area in window.screen.areas
                if area.type not in {'PROPERTIES', 'OUTLINER', 'TOPBAR', 'STATUSBAR'}
            ]
        if not candidates:
            raise RuntimeError("No suitable area is available for the Video Sequencer")
        timeline_area = max(candidates, key=lambda area: area.width * area.height)
        timeline_area.type = 'SEQUENCE_EDITOR'
        timeline_area.spaces.active.view_type = 'SEQUENCER_PREVIEW'

    space = timeline_area.spaces.active
    if hasattr(space, "show_region_ui"):
        space.show_region_ui = True
    for region in timeline_area.regions:
        if region.type != 'WINDOW':
            continue
        try:
            with bpy.context.temp_override(
                window=window,
                area=timeline_area,
                region=region,
                scene=scene,
            ):
                bpy.ops.sequencer.view_all()
        except Exception:
            pass
        break
    timeline_area.tag_redraw()
    print(
        f"[NANODE VIDEO] Video Editor focused: scene={scene.name}, "
        f"strip={getattr(target, 'name', 'none')}"
    )


def _schedule_video_editor(scene_name: str, strip_name: str = "") -> None:
    current_window = getattr(bpy.context, "window", None)
    window_pointer = current_window.as_pointer() if current_window else 0

    def _open_editor():
        scene = bpy.data.scenes.get(scene_name)
        if not scene:
            return None
        windows = list(getattr(bpy.context.window_manager, "windows", []) or [])
        window = next(
            (candidate for candidate in windows if candidate.as_pointer() == window_pointer),
            windows[0] if windows else None,
        )
        if not window:
            return None
        try:
            _focus_video_editor(window, scene, strip_name)
        except Exception as exc:
            print(f"[NANODE VIDEO] Could not focus Video Editor: {exc}")
        return None

    bpy.app.timers.register(_open_editor, first_interval=0.05)


def load_video_path_to_sequencer(
    video_path: str,
    job_id: int = 0,
    label: str = "Nanode Video",
    scene_name: str = "",
    open_editor: bool = False,
) -> str:
    scene = bpy.data.scenes.get(scene_name) if scene_name else bpy.context.scene
    if not scene:
        raise RuntimeError("Target scene is no longer available")
    video_path = bpy.path.abspath(video_path)
    if not os.path.isfile(video_path):
        raise RuntimeError("Generated video file is missing")

    sequence_editor = scene.sequence_editor_create()
    scene.render.use_sequencer = False
    strips = _editable_strip_collection(sequence_editor)
    strip_name = f"{label} #{int(job_id)}"
    sound_name = f"{strip_name} Audio"

    for strip in _all_sequence_strips(sequence_editor):
        if strip.name in {strip_name, sound_name}:
            strips.remove(strip)

    frame_start = max(1, int(scene.frame_current or scene.frame_start or 1))
    frame_end_probe = frame_start + max(1, int(scene.render.fps or 24) * 10)
    sound_channel = _next_sequence_channel(scene, frame_start, frame_end_probe, required_channels=2)
    movie_channel = sound_channel + 1

    try:
        try:
            sound_strip = strips.new_sound(
                name=sound_name,
                filepath=video_path,
                channel=sound_channel,
                frame_start=frame_start,
            )
        except TypeError:
            sound_strip = strips.new_sound(sound_name, video_path, sound_channel, frame_start)
        sound_strip.frame_start = frame_start
        sound_strip.volume = 1.0
    except Exception as exc:
        print(f"[NANODE VIDEO] Audio track could not be loaded: {exc}")
        movie_channel = sound_channel

    try:
        movie_strip = strips.new_movie(
            name=strip_name,
            filepath=video_path,
            channel=movie_channel,
            frame_start=frame_start,
        )
    except TypeError:
        movie_strip = strips.new_movie(strip_name, video_path, movie_channel, frame_start)

    movie_strip.frame_start = frame_start
    _activate_sequence_strip(scene, movie_strip.name)
    scene.frame_end = max(scene.frame_end, movie_strip.frame_final_end - 1)
    scene.frame_set(frame_start)
    props = getattr(scene, "nanode_video_director", None)
    if props:
        props.last_video_path = video_path
        try:
            _assign_source_video(props, video_path)
        except Exception as exc:
            print(f"[NANODE VIDEO] Source duration could not be cached: {exc}")
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()
    if open_editor:
        _schedule_video_editor(scene.name, movie_strip.name)
    else:
        _schedule_video_preview(scene.name, movie_strip.name)
    return video_path


def _format_video_job_status(job: dict) -> str:
    status = str(job.get("status") or "unknown")
    if status == "succeeded":
        return "Video ready"
    if status == "failed":
        return f"Video failed: {job.get('error') or 'unknown error'}"
    credits = job.get("reserved_credits") or job.get("credit_cost") or 0
    return f"{status} ({credits} credits)"


def _apply_job_response(scene_name: str, job_id: int, response: dict) -> str:
    scene = bpy.data.scenes.get(scene_name)
    if not scene or not hasattr(scene, "nanode_video_director"):
        return "missing"
    props = scene.nanode_video_director
    job = response.get("job", response)
    status = str(job.get("status") or "unknown")
    props.status = _format_video_job_status(job)
    props.output_url = job.get("output_url") or ""
    history_item = record_video_job(scene, job, source="DIRECTOR")

    if status == "succeeded" and props.output_url and props.loaded_job_id != job_id:
        try:
            path = load_video_result_to_sequencer(
                props.output_url,
                job_id,
                "Nanode Video",
                scene_name=scene_name,
            )
            props.loaded_job_id = job_id
            props.last_video_path = path
            if history_item:
                history_item.filepath = path
            props.output_url = ""
            props.status = f"Loaded in Sequencer: {os.path.basename(path)}"
        except Exception as exc:
            props.status = f"Video ready, load failed: {exc}"

    if "balance" in response and hasattr(scene, "gemini_render"):
        scene.gemini_render.beta_balance = int(response.get("balance") or 0)
    return status


def schedule_video_director_poll(scene_name: str, job_id: int) -> None:
    job_id = int(job_id or 0)
    if job_id <= 0 or job_id in _polling_job_ids:
        return
    generation = _runtime_generation
    _polling_job_ids.add(job_id)
    retries = 0

    def _poll():
        nonlocal retries
        if generation != _runtime_generation:
            _polling_job_ids.discard(job_id)
            return None
        scene = bpy.data.scenes.get(scene_name)
        if not scene:
            _polling_job_ids.discard(job_id)
            return None
        try:
            response = beta_api.get_video_job(job_id)
            status = _apply_job_response(scene_name, job_id, response)
            retries = 0
            if status in {"succeeded", "failed", "missing"}:
                _polling_job_ids.discard(job_id)
                return None
            return 10.0
        except Exception as exc:
            retries += 1
            props = getattr(scene, "nanode_video_director", None)
            if props:
                props.status = f"Status check failed ({retries}/3): {exc}"
            if retries < 3:
                return 10.0
            _polling_job_ids.discard(job_id)
            return None

    bpy.app.timers.register(_poll, first_interval=5.0)


def reset_runtime_state() -> None:
    global _runtime_generation
    _runtime_generation += 1
    _polling_job_ids.clear()


def resume_pending_jobs() -> None:
    for scene in bpy.data.scenes:
        props = getattr(scene, "nanode_video_director", None)
        if not props or props.last_job_id <= 0 or props.loaded_job_id == props.last_job_id:
            continue
        if props.status.lower().startswith("video failed"):
            continue
        schedule_video_director_poll(scene.name, props.last_job_id)


def _draw_image_slot(layout, props, attr: str, label: str, target: str) -> None:
    box = layout.box()
    box.prop(props, attr, text=label)
    row = box.row(align=True)
    op = row.operator("nanode.video_use_image", text="Editor", icon='IMAGE_DATA')
    op.target = target
    op = row.operator("nanode.video_pick_history_image", text="History", icon='TIME')
    op.target = target
    op = row.operator("nanode.video_load_image", text="", icon='FILE_FOLDER')
    op.target = target
    if getattr(props, attr):
        op = row.operator("nanode.video_clear_image", text="", icon='X')
        op.target = target


def _video_model_label(model: str) -> str:
    labels = {item[0]: item[1] for item in VIDEO_MODEL_ITEMS}
    return labels.get(model, model or "Video")


def draw_video_history(
    layout,
    context,
    omni_only: bool = False,
    show_header: bool = True,
    allow_omni_reuse: bool = False,
) -> None:
    props = _video_props(context)
    if not props:
        return

    if show_header:
        header = layout.row(align=True)
        icon = 'DISCLOSURE_TRI_DOWN' if props.show_video_history else 'DISCLOSURE_TRI_RIGHT'
        header.prop(props, "show_video_history", text="Video History", icon=icon, emboss=False)
        refresh = header.row(align=True)
        refresh.enabled = bool(_get_nanode_token(context))
        refresh.operator("nanode.video_history_refresh", text="", icon='FILE_REFRESH')
        if not props.show_video_history:
            return
    elif _get_nanode_token(context):
        refresh = layout.row(align=True)
        refresh.alignment = 'RIGHT'
        refresh.operator("nanode.video_history_refresh", text="Refresh", icon='FILE_REFRESH')

    visible = [
        index
        for index, item in enumerate(props.video_history)
        if not omni_only or is_omni_model(item.model)
    ]
    if not visible:
        layout.label(text="No generated videos", icon='INFO')
        return

    for index in reversed(visible):
        item = props.video_history[index]
        box = layout.box()
        status_icon = 'CHECKMARK' if item.status == 'succeeded' else 'ERROR' if item.status == 'failed' else 'TIME'
        row = box.row(align=True)
        row.label(text=_video_model_label(item.model), icon=status_icon)
        if item.job_id:
            row.label(text=f"#{item.job_id}")
        play = row.row(align=True)
        play.enabled = bool(
            (item.filepath and os.path.isfile(bpy.path.abspath(item.filepath)))
            or (item.status == 'succeeded' and item.output_url)
        )
        operator = play.operator("nanode.video_history_play", text="", icon='PLAY')
        operator.history_index = index
        operator = row.operator("nanode.video_history_remove", text="", icon='X')
        operator.history_index = index

        details = " / ".join(
            value
            for value in (
                item.task.replace('_', ' ').title() if item.task else "",
                item.resolution,
                f"{item.duration_seconds}s" if item.duration_seconds else "",
                item.aspect_ratio,
            )
            if value
        )
        if details:
            box.label(text=details, icon='SEQUENCE')
        meta = []
        if item.credit_cost:
            meta.append(f"{item.credit_cost} credits")
        if item.created_at:
            meta.append(item.created_at.replace('T', ' ')[:19])
        if meta:
            box.label(text=" | ".join(meta))
        if item.error:
            error_row = box.row()
            error_row.alert = True
            error_row.label(text=item.error[:120], icon='ERROR')
        if allow_omni_reuse and item.source == 'OMNI_ENGINE':
            reuse = box.row()
            source_path = bpy.path.abspath(item.source_video_path) if item.source_video_path else ""
            reuse.enabled = bool(source_path and os.path.isfile(source_path))
            operator = reuse.operator(
                "nanode.video_history_reuse_omni",
                text="Reuse Source & Prompt",
                icon='RECOVER_LAST',
            )
            operator.history_index = index


def _draw_video_director(layout, context) -> None:
    props = _video_props(context)
    if not props:
        layout.label(text="Video Director is unavailable", icon='ERROR')
        return

    layout.use_property_split = True
    layout.use_property_decorate = False
    layout.prop(props, "model")
    layout.prop(props, "prompt", text="Prompt")
    layout.prop(props, "task")
    layout.prop(props, "resolution")
    layout.prop(props, "aspect_ratio")

    duration_row = layout.row()
    duration_row.enabled = is_omni_model(props.model) or (
        props.resolution == '720p' and props.task not in {'first_last', 'reference_to_video'}
    )
    duration_row.prop(props, "duration")

    continuation = layout.box()
    continuation.label(text="Continue Timeline Video", icon='SEQUENCE')
    continue_row = continuation.row(align=True)
    continue_row.enabled = _visible_sequence_strip_at_frame(context.scene, int(context.scene.frame_current)) is not None
    continue_row.operator(
        "nanode.video_continue_from_playhead",
        text=f"Use Playhead Frame {context.scene.frame_current}",
        icon='KEYFRAME_HLT',
    )
    if props.continuation_source_frame and props.input_image:
        continuation.label(
            text=f"First Frame: {props.input_image.name}",
            icon='IMAGE_DATA',
        )

    if props.task in {'image_to_video', 'first_last'}:
        _draw_image_slot(layout, props, "input_image", "First Frame", "FIRST")
    if props.task == 'first_last':
        _draw_image_slot(layout, props, "last_frame_image", "Last Frame", "LAST")
    if props.task == 'reference_to_video':
        _draw_image_slot(layout, props, "reference_image", "Reference 1", "REFERENCE_1")
        _draw_image_slot(layout, props, "reference_image_2", "Reference 2", "REFERENCE_2")
        _draw_image_slot(layout, props, "reference_image_3", "Reference 3", "REFERENCE_3")
    if is_omni_model(props.model) and props.task == 'edit':
        box = layout.box()
        box.prop(props, "source_video_path", text="Source Video")
        row = box.row(align=True)
        row.operator("nanode.video_load_source", text="Choose Video", icon='FILE_MOVIE')
        use_last = row.row(align=True)
        use_last.enabled = bool(props.last_video_path and os.path.isfile(bpy.path.abspath(props.last_video_path)))
        use_last.operator("nanode.video_use_last_result", text="Use Last", icon='RECOVER_LAST')

    validation_error = _model_validation_error(props)
    if validation_error:
        row = layout.row()
        row.alert = True
        row.label(text=validation_error, icon='ERROR')

    duration = _effective_duration(props)
    cost = get_video_cost(props.model, props.task, props.resolution, duration)
    price_row = layout.row()
    if cost is None:
        price_row.alert = True
        price_row.label(text="Unsupported model / resolution", icon='ERROR')
    else:
        forced = " (8s required)" if duration == 8 and int(props.duration) != 8 else ""
        price_row.label(text=f"Estimated: {cost} credits{forced}", icon='SEQUENCE')

    token = _get_configured_token(context)
    is_nanode = auth_utils.is_nanode_token(token)
    is_personal = auth_utils.is_google_api_key(token)
    if not token:
        row = layout.row()
        row.alert = True
        row.operator("banana.google_login", text="Login with Google", icon='URL')
    elif is_nanode:
        account = layout.row(align=True)
        scene_props = getattr(context.scene, "gemini_render", None)
        if scene_props and scene_props.beta_balance >= 0:
            account.label(text=f"Credits: {scene_props.beta_balance}")
        else:
            account.label(text="Nanode Account", icon='LINKED')
        account.operator("banana.refresh_balance", text="", icon='FILE_REFRESH')
        account.operator("banana.open_store", text="Buy Credits", icon='PLUS')
    elif is_omni_model(props.model):
        layout.label(text="Personal Google API / no Nanode credits", icon='PREFERENCES')
    else:
        row = layout.row()
        row.alert = True
        row.label(text="Personal API mode supports Gemini Omni here", icon='ERROR')

    action = layout.row()
    action.scale_y = 1.3
    auth_supported = is_nanode or (is_personal and is_omni_model(props.model))
    action.enabled = bool(auth_supported and props.prompt.strip() and not validation_error and cost is not None)
    action.operator("nanode.video_director_submit", text="Generate Video", icon='RENDER_ANIMATION')

    if props.last_job_id:
        row = layout.row(align=True)
        row.label(text=f"Job #{props.last_job_id}", icon='TIME')
        row.operator("nanode.video_director_refresh", text="", icon='FILE_REFRESH')
    if props.status:
        layout.label(text=props.status, icon='INFO')
    layout.separator()
    draw_video_history(layout, context)


def _draw_video_editor(layout, context) -> None:
    props = _video_props(context)
    if not props:
        layout.label(text="AI Video Editor is unavailable", icon='ERROR')
        return

    layout.use_property_split = True
    layout.use_property_decorate = False

    source_exists = os.path.isfile(bpy.path.abspath(props.source_video_path))
    validation_error = ""
    if not source_exists:
        validation_error = "Select a source video or Movie Strip"
    elif props.use_style_reference and not props.style_reference_image:
        validation_error = "Select a style reference image or disable Style Reference"
    duration = 10
    detected_duration = 0.0
    if source_exists:
        detected_duration = _detected_source_duration(props, allow_probe=False)
        if props.edit_duration == 'AUTO':
            if detected_duration > 0.0:
                duration = _nearest_omni_duration(detected_duration)
        else:
            duration = int(props.edit_duration)
    duration_error = _edit_duration_validation_error(props, allow_probe=False)
    if duration_error:
        validation_error = duration_error
    cost = get_video_cost('gemini-omni-flash-preview', 'edit', '720p', duration)
    token = _get_configured_token(context)
    is_nanode = auth_utils.is_nanode_token(token)
    is_personal = auth_utils.is_google_api_key(token)

    model = layout.row()
    model.label(text="Model")
    model.label(text="Gemini Omni Flash")
    if is_personal:
        layout.label(text="Personal Google API / 720p", icon='PREFERENCES')
    else:
        layout.label(text=f"Cost: {cost} credits per edit")
    if props.edit_duration == 'AUTO' and detected_duration > 0.0:
        layout.label(
            text=f"Auto duration: {duration}s (source {detected_duration:.2f}s)",
            icon='TIME',
        )

    if not token:
        row = layout.row()
        row.alert = True
        row.operator("banana.google_login", text="Login with Google", icon='URL')
    elif is_nanode:
        account = layout.row(align=True)
        scene_props = getattr(context.scene, "gemini_render", None)
        balance = getattr(scene_props, "beta_balance", -1) if scene_props else -1
        account.label(text=f"Credits: {balance}" if balance >= 0 else "Nanode Account")
        account.operator("banana.refresh_balance", text="", icon='FILE_REFRESH')
        account.operator("banana.open_store", text="Buy Credits", icon='PLUS')

    if validation_error:
        warning = layout.row()
        warning.alert = True
        warning.label(text=validation_error, icon='ERROR')

    action = layout.row()
    action.scale_y = 1.3
    action.enabled = bool((is_nanode or is_personal) and props.prompt.strip() and not validation_error)
    action.operator("nanode.video_editor_submit", text="Edit Video", icon='RENDER_ANIMATION')

    if props.status and props.status != "Ready":
        layout.separator()
        status_box = layout.box()
        status_value = props.status.lower()
        status_icon = 'ERROR' if "failed" in status_value else 'CHECKMARK' if "ready" in status_value else 'TIME'
        status = status_box.row(align=True)
        label = f"Job #{props.last_job_id}: {props.status}" if props.last_job_id else props.status
        status.label(text=label, icon=status_icon)
        if props.last_job_id:
            status.operator("nanode.video_director_refresh", text="", icon='FILE_REFRESH')


class NANODE_PT_VideoDirector3D(Panel):
    bl_label = "AI Video Director"
    bl_idname = "NANODE_PT_video_director_3d"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Nanode Video"

    def draw(self, context):
        _draw_video_director(self.layout, context)


class NANODE_PT_VideoDirectorSequencer(Panel):
    bl_label = "AI Video Generation"
    bl_idname = "NANODE_PT_video_director_sequencer"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Nanode Video"
    bl_order = 10
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        _draw_video_director(self.layout, context)


class NANODE_PT_VideoEditorSequencer(Panel):
    bl_label = "AI Video Editor"
    bl_idname = "NANODE_PT_video_editor_sequencer"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Nanode Video"
    bl_order = 0

    def draw(self, context):
        _draw_video_editor(self.layout, context)


class NANODE_PT_VideoEditorPrompt(Panel):
    bl_label = "Prompt"
    bl_idname = "NANODE_PT_video_editor_prompt"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Nanode Video"
    bl_parent_id = "NANODE_PT_video_editor_sequencer"
    bl_order = 0

    def draw(self, context):
        props = _video_props(context)
        if props:
            self.layout.prop(props, "prompt", text="")


class NANODE_PT_VideoEditorInput(Panel):
    bl_label = "Video Input"
    bl_idname = "NANODE_PT_video_editor_input"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Nanode Video"
    bl_parent_id = "NANODE_PT_video_editor_sequencer"
    bl_order = 1

    def draw(self, context):
        props = _video_props(context)
        if not props:
            return
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(props, "source_video_path", text="Source")

        selected = layout.row()
        selected.enabled = _selected_movie_strip(context) is not None
        selected.operator("nanode.video_use_selected_strip", text="Use Selected Clip", icon='FILE_MOVIE')
        sources = layout.row(align=True)
        sources.operator("nanode.video_load_source", text="Choose File", icon='FILE_FOLDER')
        use_last = sources.row(align=True)
        use_last.enabled = bool(
            props.last_video_path and os.path.isfile(bpy.path.abspath(props.last_video_path))
        )
        use_last.operator("nanode.video_use_last_result", text="Last Result", icon='RECOVER_LAST')

        layout.separator()
        layout.prop(props, "edit_duration")
        layout.prop(props, "edit_aspect_ratio")
        notice = layout.row()
        notice.alert = True
        notice.label(text="Output supports 16:9 and 9:16 only", icon='INFO')


class NANODE_PT_VideoEditorStyle(Panel):
    bl_label = "Style Reference"
    bl_idname = "NANODE_PT_video_editor_style"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Nanode Video"
    bl_parent_id = "NANODE_PT_video_editor_sequencer"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    def draw_header(self, context):
        props = _video_props(context)
        if props:
            self.layout.prop(props, "use_style_reference", text="")

    def draw(self, context):
        props = _video_props(context)
        if not props:
            return
        layout = self.layout
        layout.active = props.use_style_reference
        layout.prop(props, "style_reference_image", text="Image")
        row = layout.row(align=True)
        operator = row.operator("nanode.video_use_image", text="Editor", icon='IMAGE_DATA')
        operator.target = 'STYLE'
        operator = row.operator("nanode.video_pick_history_image", text="History", icon='TIME')
        operator.target = 'STYLE'
        operator = row.operator("nanode.video_load_image", text="", icon='FILE_FOLDER')
        operator.target = 'STYLE'
        if props.style_reference_image:
            operator = row.operator("nanode.video_clear_image", text="", icon='X')
            operator.target = 'STYLE'


class NANODE_PT_VideoEditorHistory(Panel):
    bl_label = "Video History"
    bl_idname = "NANODE_PT_video_editor_history"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Nanode Video"
    bl_parent_id = "NANODE_PT_video_editor_sequencer"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3

    def draw(self, context):
        draw_video_history(
            self.layout,
            context,
            omni_only=True,
            show_header=False,
        )


class NANODE_PT_VideoFramesImageEditor(Panel):
    bl_label = "Video Frames"
    bl_idname = "NANODE_PT_video_frames_image_editor"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Nanode Video"

    def draw(self, context):
        layout = self.layout
        image = getattr(context.space_data, "image", None)
        if image:
            layout.label(text=image.name, icon='IMAGE_DATA')
        else:
            layout.label(text="No image selected", icon='ERROR')

        column = layout.column(align=True)
        column.enabled = image is not None
        for target, label in (
            ('FIRST', "Use as First Frame"),
            ('LAST', "Use as Last Frame"),
            ('REFERENCE_1', "Use as Reference 1"),
            ('REFERENCE_2', "Use as Reference 2"),
            ('REFERENCE_3', "Use as Reference 3"),
            ('STYLE', "Use as Video Style"),
        ):
            operator = column.operator("nanode.video_use_image", text=label, icon='ADD')
            operator.target = target


classes = (
    VideoHistoryItem,
    VideoDirectorProperties,
    NanodeOTUseVideoImage,
    NanodeOTPickHistoryImage,
    NanodeOTUseRenderHistoryImage,
    NanodeOTLoadVideoImage,
    NanodeOTLoadSourceVideo,
    NanodeOTUseLastVideo,
    NanodeOTUseSelectedVideoStrip,
    NanodeOTContinueFromPlayhead,
    NanodeOTClearVideoImage,
    NanodeOTSubmitDirectorJob,
    NanodeOTSubmitVideoEdit,
    NanodeOTRefreshDirectorJob,
    NanodeOTRefreshVideoHistory,
    NanodeOTPlayVideoHistory,
    NanodeOTRemoveVideoHistory,
    NanodeOTReuseOmniHistory,
    NanodeOTClearOmniReuseSource,
    NANODE_PT_VideoDirector3D,
    NANODE_PT_VideoDirectorSequencer,
    NANODE_PT_VideoEditorSequencer,
    NANODE_PT_VideoEditorPrompt,
    NANODE_PT_VideoEditorInput,
    NANODE_PT_VideoEditorStyle,
    NANODE_PT_VideoEditorHistory,
    NANODE_PT_VideoFramesImageEditor,
)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
    if hasattr(bpy.types.WindowManager, "nanode_video_director"):
        del bpy.types.WindowManager.nanode_video_director
    bpy.types.Scene.nanode_video_director = PointerProperty(type=VideoDirectorProperties)


def unregister() -> None:
    reset_runtime_state()
    if hasattr(bpy.types.Scene, "nanode_video_director"):
        del bpy.types.Scene.nanode_video_director
    if hasattr(bpy.types.WindowManager, "nanode_video_director"):
        del bpy.types.WindowManager.nanode_video_director
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
