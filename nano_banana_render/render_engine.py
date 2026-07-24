"""
Custom Render Engine for Nano Banana
Registers 'Nano Banana' in Blender's Render Engine dropdown.

Architecture:
  F12 → BananaOTRender (pre-captures viewport via opengl) →
  stores path → triggers bpy.ops.render.render →
  NanoBananaRenderEngine.render() picks up stored capture →
  calls Gemini API → loads result

This avoids the render-lock issue where opengl() fails during F12.
"""

import bpy
import os
import time
import tempfile
import shutil
import json
import re
import uuid
from datetime import datetime

from . import auth_utils
from .model_config import MODEL_MAP, supports_image_resolution

# Model name mapping

# Module-level storage for pre-captured viewport image
_pre_capture = {
    'path': None,
    'ready': False,
    'engine': None,
    'media_type': 'image',
    'source_mode': 'EEVEE',
    'input_mode': 'FRAME',
    'reference_paths': [],
    'style_reference_index': None,
    'temp_dir': None,
    'debug_path': None,
    'request_id': None,
}

NANODE_RENDER_ENGINES = {'NANO_BANANA', 'NANODE_OMNI'}
_omni_polling_job_ids = set()
_omni_runtime_generation = 0
_omni_submission_active = False
_omni_autotrigger_pending = False
_omni_last_submission_finished_at = 0.0
_OMNI_SUBMISSION_COOLDOWN_SECONDS = 5.0


def _begin_omni_submission():
    global _omni_submission_active
    if (
        _omni_submission_active
        or time.monotonic() - _omni_last_submission_finished_at < _OMNI_SUBMISSION_COOLDOWN_SECONDS
    ):
        return False
    _omni_submission_active = True
    return True


def _finish_omni_submission(apply_cooldown=True):
    global _omni_submission_active, _omni_last_submission_finished_at
    _omni_submission_active = False
    if apply_cooldown:
        _omni_last_submission_finished_at = time.monotonic()
    else:
        _omni_last_submission_finished_at = 0.0


class BananaOTRender(bpy.types.Operator):
    """Pre-capture viewport, then trigger F12 render engine"""
    bl_idname = "banana.ai_render"
    bl_label = "AI Render"
    bl_description = "Render using Nano Banana AI"

    def execute(self, context):
        scene = context.scene
        engine = scene.render.engine

        # If not Nano Banana engine, fall through to standard render
        if engine not in NANODE_RENDER_ENGINES:
            bpy.ops.render.render('INVOKE_DEFAULT')
            return {'FINISHED'}

        props = scene.gemini_render if hasattr(scene, 'gemini_render') else None
        if not props:
            self.report({'ERROR'}, "Nano Banana properties not found")
            return {'CANCELLED'}

        # Validate beta token
        prefs = context.preferences.addons.get("nano_banana_render")
        token = ""
        if prefs and hasattr(prefs.preferences, 'beta_token'):
            token = prefs.preferences.beta_token.strip()
        if not token:
            self.report({'ERROR'}, "No beta token. Go to Edit → Preferences → Add-ons → Nano Banana")
            return {'CANCELLED'}

        if not scene.camera:
            self.report({'ERROR'}, "No active camera in scene")
            return {'CANCELLED'}

        if not props.prompt.strip() or len(props.prompt.strip()) < 10:
            self.report({'ERROR'}, "Prompt too short (minimum 10 characters)")
            return {'CANCELLED'}

        if engine == 'NANO_BANANA' and auth_utils.is_nanode_token(token):
            from . import beta_api
            try:
                account = beta_api.validate_nanode_token()
                if "balance" in account:
                    props.beta_balance = int(account.get("balance") or 0)
            except beta_api.BetaAPIError as exc:
                if beta_api.is_invalid_token_error(exc):
                    message = "Nanode login expired. Log in with Google again."
                else:
                    message = f"Nanode server check failed: {exc.message}"
                props.status_text = message
                self.report({'ERROR'}, message)
                return {'CANCELLED'}

        if engine == 'NANODE_OMNI':
            is_nanode = auth_utils.is_nanode_token(token)
            is_personal = auth_utils.is_google_api_key(token)
            if not is_nanode and not is_personal:
                self.report({'ERROR'}, "Configure Nanode Login or a personal Google API key for Omni Engine")
                return {'CANCELLED'}

            if is_nanode:
                from . import beta_api
                try:
                    account = beta_api.validate_nanode_token()
                    if "balance" in account:
                        props.beta_balance = int(account.get("balance") or 0)
                except beta_api.BetaAPIError as exc:
                    if beta_api.is_invalid_token_error(exc):
                        message = "Nanode login expired. Log in with Google again."
                    else:
                        message = f"Nanode server check failed: {exc.message}"
                    _set_omni_status(scene, message)
                    self.report({'ERROR'}, message)
                    return {'CANCELLED'}

            if not _begin_omni_submission():
                message = "Omni submission is busy. Wait a few seconds before trying again."
                _set_omni_status(scene, message)
                self.report({'WARNING'}, message)
                return {'CANCELLED'}

            _pre_capture['ready'] = False
            _pre_capture['path'] = None
            _pre_capture['reference_paths'] = []
            _pre_capture['style_reference_index'] = None
            _pre_capture['temp_dir'] = None
            _pre_capture['debug_path'] = None
            _pre_capture['request_id'] = uuid.uuid4().hex

            try:
                capture = _prepare_omni_capture(scene, props)
                _pre_capture.update(capture)
                _pre_capture['engine'] = 'NANODE_OMNI'
                _pre_capture['ready'] = True
                print(f"[NANODE OMNI] Pre-capture done: {capture.get('path')}")
                if capture.get("debug_path"):
                    _set_omni_status(scene, f"Source video saved: {capture.get('debug_path')}")
            except Exception as e:
                _finish_omni_submission()
                self.report({'ERROR'}, f"Omni capture failed: {e}")
                return {'CANCELLED'}

            try:
                result = bpy.ops.render.render('INVOKE_DEFAULT')
            except Exception:
                _cleanup_capture()
                _finish_omni_submission()
                raise
            if 'CANCELLED' in result:
                _cleanup_capture()
                _finish_omni_submission()
                self.report({'ERROR'}, "Omni render could not be started")
                return {'CANCELLED'}
            return {'FINISHED'}

        if not supports_image_resolution(props.ai_model, getattr(props, "resolution", "1024")):
            self.report({'ERROR'}, "Selected model supports 1K only")
            return {'CANCELLED'}

        # --- Step 1: Pre-capture viewport (NO render lock here!) ---
        from . import depth_utils
        depth_renderer = depth_utils.DepthRenderer()

        _pre_capture['ready'] = False
        _pre_capture['path'] = None
        _pre_capture['engine'] = None
        _pre_capture['reference_paths'] = []
        _pre_capture['style_reference_index'] = None
        _pre_capture['temp_dir'] = None
        _pre_capture['debug_path'] = None

        try:
            if props.render_mode == 'DEPTH':
                print("[NANO BANANA] Pre-capturing depth map...")
                path = depth_renderer.render_depth_map_mist(
                    scene, props.mist_start, props.mist_depth, props.mist_falloff
                )
            else:
                print("[NANO BANANA] Pre-capturing EEVEE viewport...")
                path = depth_renderer.render_regular_eevee(scene)

            _pre_capture['path'] = path
            _pre_capture['ready'] = True
            _pre_capture['engine'] = 'NANO_BANANA'
            _pre_capture['media_type'] = 'image'
            _pre_capture['source_mode'] = props.render_mode
            _pre_capture['input_mode'] = 'FRAME'
            print(f"[NANO BANANA] Pre-capture done: {path}")

        except Exception as e:
            self.report({'ERROR'}, f"Viewport capture failed: {e}")
            try:
                depth_renderer.cleanup_temp_files()
            except Exception:
                pass
            return {'CANCELLED'}

        # --- Step 2: Trigger F12 render (engine picks up stored capture) ---
        bpy.ops.render.render('INVOKE_DEFAULT')

        return {'FINISHED'}


class NanoBananaRenderEngine(bpy.types.RenderEngine):
    """Custom render engine — uses pre-captured viewport data from BananaOTRender"""
    bl_idname = 'NANO_BANANA'
    bl_label = 'Nano Banana'
    bl_use_preview = False
    bl_use_shading_nodes_custom = False
    bl_use_eevee_viewport = True
    bl_use_gpu_context = False

    def render(self, depsgraph):
        """
        Called by Blender after BananaOTRender pre-captured the viewport.
        Reads the stored capture, calls Gemini API, writes result into F12 viewer.
        """
        render_start = time.time()
        scene = depsgraph.scene
        props = scene.gemini_render if hasattr(scene, 'gemini_render') else None

        if self.is_preview:
            return  # Nano Banana does not support rendering material preview spheres

        if not props:
            self.report({'ERROR'}, "Nano Banana properties not found")
            return

        if self.is_animation:
            message = "Render Animation is disabled for Nano Banana. Use AI Render once."
            live_scene = bpy.data.scenes.get(scene.name)
            if live_scene and hasattr(live_scene, "gemini_render"):
                live_scene.gemini_render.status_text = message
            _pre_capture['ready'] = False
            self.report({'ERROR'}, message)
            raise RuntimeError(message)

        # Check for pre-captured viewport data
        if not _pre_capture.get('ready') or not _pre_capture.get('path') or _pre_capture.get('engine') != 'NANO_BANANA':
            # Called from menu (Render → Render Image) without pre-capture.
            # Return empty result, then schedule our operator to do it properly.
            render_w = int(scene.render.resolution_x * scene.render.resolution_percentage / 100)
            render_h = int(scene.render.resolution_y * scene.render.resolution_percentage / 100)
            result = self.begin_result(0, 0, render_w, render_h)
            self.end_result(result)

            def _trigger_proper_render():
                try:
                    bpy.ops.banana.ai_render()
                except Exception as e:
                    print(f"[NANO BANANA] Auto-trigger failed: {e}")
                return None  # Don't repeat

            bpy.app.timers.register(_trigger_proper_render, first_interval=0.5)
            return

        depth_path = _pre_capture['path']
        _pre_capture['ready'] = False  # Consume

        # Validate beta token
        from . import beta_api

        from . import threading_utils

        render_mode = props.render_mode
        model_name = MODEL_MAP.get(props.ai_model, 'gemini-3.1-flash-image')

        # --- Call via Beta Server ---
        gen_type = 'render_eevee' if render_mode == 'EEVEE' else 'render_depth'
        if render_mode == 'DEPTH':
            self.update_stats("", f"Sending depth map to {model_name}...")
        else:
            self.update_stats("", f"Sending image to {model_name}...")

        reference_path = threading_utils.save_reference_image_temp(scene)

        # Determine dimensions from scene render settings and addon UI property
        render = scene.render
        base_res = int(props.resolution) if hasattr(props, 'resolution') else 1024
        scene_aspect = render.resolution_x / render.resolution_y if render.resolution_y > 0 else 1.0
        
        if scene_aspect >= 1:
            width = base_res
            height = int(base_res / scene_aspect)
        else:
            width = int(base_res * scene_aspect)
            height = base_res

        # Determine token for direct vs server API
        token = ""
        prefs = bpy.context.preferences.addons.get("nano_banana_render")
        if prefs and hasattr(prefs.preferences, "beta_token"):
            token = prefs.preferences.beta_token.strip()

        try:
            if auth_utils.is_google_api_key(token):
                # ─── Direct Google API Mode ───
                from .gemini_api import GeminiAPI, GeminiAPIError
                
                # Turn off beta UI elements for API key users
                def _update_direct_ui():
                    if hasattr(scene, 'gemini_render'):
                        scene.gemini_render.beta_balance = -1  # Hide balance
                        scene.gemini_render.last_generation_id = 0
                        scene.gemini_render.last_generation_rated = False
                threading_utils.execute_in_main_thread(_update_direct_ui)
                
                self.update_stats("", "Connecting directly to Google API...")
                gemini = GeminiAPI(api_key=token, model=model_name)
                is_color = (render_mode == 'EEVEE')
                image_data, _ = gemini.generate_image(
                    depth_image_path=depth_path,
                    user_prompt=props.prompt,
                    reference_image_path=reference_path,
                    is_color_render=is_color,
                    width=width,
                    height=height
                )
                
            else:
                # ─── Server Mode (Nanode API) ───
                # Build prompt client-side (same logic as direct mode)
                from .gemini_api import GeminiAPI
                is_color = (render_mode == 'EEVEE')
                prompt_builder = GeminiAPI.__new__(GeminiAPI)
                full_prompt = prompt_builder._build_prompt(
                    props.prompt,
                    has_reference=bool(reference_path),
                    is_color_render=is_color
                )
                
                image_data, generation_id, new_balance = beta_api.generate(
                    prompt=full_prompt,
                    model=model_name,
                    input_image_path=depth_path,
                    reference_image_path=reference_path,
                    gen_type=gen_type,
                    width=width,
                    height=height,
                    user_prompt=props.prompt,
                )
    
                # Update balance and generation tracking for rating UI
                def _update_beta_ui():
                    if hasattr(scene, 'gemini_render'):
                        scene.gemini_render.beta_balance = new_balance
                        scene.gemini_render.last_generation_id = int(generation_id) if generation_id else 0
                        scene.gemini_render.last_generation_rated = False
                threading_utils.execute_in_main_thread(_update_beta_ui)

        except beta_api.BetaAPIError as e:
            if e.status_code == 402:
                # Not enough credits — show popup
                try:
                    import json
                    detail = json.loads(e.message) if isinstance(e.message, str) and e.message.startswith('{') else {}
                    credits_needed = detail.get('credits_needed', 0)
                    credits_available = detail.get('credits_available', 0)
                except (ValueError, KeyError):
                    credits_needed = 0
                    credits_available = 0
                
                def _show_popup():
                    try:
                        bpy.ops.banana.show_no_credits_popup(
                            'INVOKE_DEFAULT',
                            credits_needed=credits_needed,
                            credits_available=credits_available
                        )
                    except Exception as ex:
                        print(f"[NANO BANANA] Popup error: {ex}")
                
                threading_utils.execute_in_main_thread(_show_popup)
                self.report({'ERROR'}, f"Not enough credits: need {credits_needed}, have {credits_available}")
            else:
                self.report({'ERROR'}, f"Beta server: {e.message}")
            return
            
        except Exception as e:
            if type(e).__name__ == "GeminiAPIError":
                self.report({'ERROR'}, f"Google API Error: {str(e)}")
            else:
                self.report({'ERROR'}, f"AI generation failed: {str(e)}")
            return
        finally:
            if reference_path:
                try:
                    os.unlink(reference_path)
                except OSError:
                    pass
            from . import depth_utils
            try:
                depth_utils.DepthRenderer().cleanup_temp_files()
            except Exception:
                pass

        if self.test_break():
            return

        # --- Validate image data ---
        if not image_data or len(image_data) < 100:
            self.report({'ERROR'}, f"AI returned empty or invalid image ({len(image_data) if image_data else 0} bytes)")
            return

        # --- Display AI result directly in F12 render buffer ---
        self.update_stats("", "Loading AI result...")

        render_w = int(scene.render.resolution_x * scene.render.resolution_percentage / 100)
        render_h = int(scene.render.resolution_y * scene.render.resolution_percentage / 100)

        self._write_image_to_render_buffer(image_data, render_w, render_h)

        elapsed = time.time() - render_start
        
        def _process_result_main_thread():
            _finalize_render_in_main_thread(image_data, props.prompt, scene, elapsed)

        threading_utils.execute_in_main_thread(_process_result_main_thread)

        self.update_stats("", f"AI render completed in {elapsed:.1f}s")


    def _write_image_to_render_buffer(self, image_data: bytes, render_w: int, render_h: int):
        """Write encoded image bytes into Blender's F12 render buffer."""
        from array import array

        temp_path = None
        temp_image = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as file:
                file.write(image_data)
                temp_path = file.name

            temp_image = bpy.data.images.load(temp_path, check_existing=False)
            if tuple(temp_image.size) != (render_w, render_h):
                temp_image.scale(render_w, render_h)

            pixel_count = render_w * render_h
            channels = max(1, int(temp_image.channels))
            source = array('f', [0.0]) * (pixel_count * channels)
            temp_image.pixels.foreach_get(source)

            if channels == 4:
                rgba = source
            else:
                rgba = array('f', [0.0]) * (pixel_count * 4)
                for index in range(pixel_count):
                    source_offset = index * channels
                    target_offset = index * 4
                    value = source[source_offset]
                    rgba[target_offset] = value
                    rgba[target_offset + 1] = source[source_offset + 1] if channels > 1 else value
                    rgba[target_offset + 2] = source[source_offset + 2] if channels > 2 else value
                    rgba[target_offset + 3] = source[source_offset + 3] if channels > 3 else 1.0

            result = self.begin_result(0, 0, render_w, render_h)
            result.layers[0].passes["Combined"].rect.foreach_set(rgba)
            self.end_result(result)
        except Exception as e:
            print(f"[NANO BANANA] Render buffer write failed: {e}")
            try:
                result = self.begin_result(0, 0, render_w, render_h)
                self.end_result(result)
            except Exception as fallback_error:
                print(f"[NANO BANANA] Empty render buffer fallback failed: {fallback_error}")
        finally:
            if temp_image and temp_image.name in bpy.data.images:
                bpy.data.images.remove(temp_image)
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass


def _normalize_video_aspect_ratio(value: str) -> str:
    return value if value in {"16:9", "9:16"} else "16:9"


def _aspect_ratio_value(aspect_ratio: str) -> float:
    aspect_ratio = _normalize_video_aspect_ratio(aspect_ratio)
    width, height = aspect_ratio.split(":", 1)
    return float(width) / float(height)


def apply_omni_camera_aspect(scene, aspect_ratio: str) -> str:
    aspect_ratio = _normalize_video_aspect_ratio(aspect_ratio)
    render = scene.render
    if aspect_ratio == "9:16":
        render.resolution_x = 720
        render.resolution_y = 1280
    else:
        render.resolution_x = 1280
        render.resolution_y = 720
    render.pixel_aspect_x = 1.0
    render.pixel_aspect_y = 1.0
    return aspect_ratio


def _set_omni_status(scene, status: str, job_id: int = 0, output_url: str = None):
    def _update():
        if hasattr(scene, "gemini_render"):
            scene.gemini_render.omni_status = status
            if job_id:
                scene.gemini_render.omni_last_job_id = job_id
            if output_url is not None:
                scene.gemini_render.omni_output_url = output_url
        return None

    try:
        from . import threading_utils
        threading_utils.execute_in_main_thread(_update)
    except Exception:
        _update()


def _format_video_job_status(job: dict) -> str:
    status = str(job.get("status") or "unknown")
    if status == "succeeded":
        return "Omni video ready"
    if status == "failed":
        return f"Omni failed: {job.get('error') or 'unknown error'}"
    credits = job.get("reserved_credits") or job.get("credit_cost") or 0
    return f"Omni {status} ({credits} credits)"


def _schedule_omni_job_poll(scene_name: str, job_id: int):
    job_id = int(job_id or 0)
    if job_id <= 0 or job_id in _omni_polling_job_ids:
        return
    generation = _omni_runtime_generation
    _omni_polling_job_ids.add(job_id)

    def _poll():
        if generation != _omni_runtime_generation:
            _omni_polling_job_ids.discard(job_id)
            return None
        try:
            from . import beta_api

            scene = bpy.data.scenes.get(scene_name)
            if not scene:
                _omni_polling_job_ids.discard(job_id)
                return None
            response = beta_api.get_video_job(job_id)
            job = response.get("job", response)
            from .video_director import record_video_job

            history_item = record_video_job(scene, job, source="OMNI_ENGINE")
            status = str(job.get("status") or "unknown")
            output_url = job.get("output_url") or ""
            if status == "succeeded" and output_url:
                try:
                    from .video_director import load_video_result_to_sequencer
                    path = load_video_result_to_sequencer(
                        output_url,
                        job_id,
                        "Nanode Omni",
                        scene_name=scene_name,
                    )
                    if history_item:
                        history_item.filepath = path
                    _set_omni_status(
                        scene,
                        f"Omni video loaded in Blender: {os.path.basename(path)}",
                        job_id,
                        "",
                    )
                except Exception as exc:
                    _set_omni_status(scene, f"Omni ready, load failed: {exc}", job_id, output_url)
            else:
                _set_omni_status(scene, _format_video_job_status(job), job_id, output_url)
            if "balance" in response and hasattr(scene, "gemini_render"):
                scene.gemini_render.beta_balance = int(response.get("balance") or 0)

            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    area.tag_redraw()

            if status in {"succeeded", "failed"}:
                _omni_polling_job_ids.discard(job_id)
                return None
            return 10.0
        except Exception as exc:
            scene = bpy.data.scenes.get(scene_name)
            if scene:
                _set_omni_status(scene, f"Omni polling failed: {exc}", job_id)
            _omni_polling_job_ids.discard(job_id)
            return None

    bpy.app.timers.register(_poll, first_interval=5.0)


def _capture_dimensions(scene, base_res: int = 1024, aspect_ratio: str = "") -> tuple[int, int]:
    render = scene.render
    aspect = (
        _aspect_ratio_value(aspect_ratio)
        if aspect_ratio
        else render.resolution_x / render.resolution_y if render.resolution_y > 0 else 1.0
    )
    if aspect >= 1.0:
        return base_res, max(1, int(base_res / aspect))
    return max(1, int(base_res * aspect)), base_res


def _even_dimension(value: int) -> int:
    value = max(2, int(value))
    return value if value % 2 == 0 else value - 1


def _capture_video_dimensions(scene, base_height: int = 720, aspect_ratio: str = "") -> tuple[int, int]:
    render = scene.render
    aspect = (
        _aspect_ratio_value(aspect_ratio)
        if aspect_ratio
        else render.resolution_x / render.resolution_y if render.resolution_y > 0 else 16 / 9
    )
    if aspect >= 1.0:
        return _even_dimension(round(base_height * aspect)), _even_dimension(base_height)
    return _even_dimension(base_height), _even_dimension(round(base_height / aspect))


def _duration_frame_count(scene, duration_seconds: int) -> int:
    fps_base = getattr(scene.render, "fps_base", 1.0) or 1.0
    fps = float(getattr(scene.render, "fps", 24)) / float(fps_base)
    return max(1, int(round(float(duration_seconds) * fps)))


def _get_viewport_context(scene):
    from . import texture_pipeline as pipe

    override = pipe._get_viewport_context()
    if not override:
        raise RuntimeError("No 3D viewport available for Omni capture")
    override["scene"] = scene
    return override


def _store_omni_output_settings(scene) -> dict:
    render = scene.render
    settings = render.image_settings
    ffmpeg = render.ffmpeg
    return {
        "media_type": getattr(settings, "media_type", "IMAGE"),
        "file_format": settings.file_format,
        "color_mode": settings.color_mode,
        "color_depth": settings.color_depth,
        "ffmpeg_format": ffmpeg.format,
        "ffmpeg_codec": ffmpeg.codec,
        "constant_rate_factor": ffmpeg.constant_rate_factor,
        "ffmpeg_preset": ffmpeg.ffmpeg_preset,
        "use_autosplit": ffmpeg.use_autosplit,
    }


def _restore_omni_output_settings(scene, settings_snapshot: dict):
    render = scene.render
    settings = render.image_settings
    if hasattr(settings, "media_type"):
        try:
            settings.media_type = settings_snapshot.get("media_type", "IMAGE")
        except TypeError:
            pass

    for attr in ("file_format", "color_mode", "color_depth"):
        value = settings_snapshot.get(attr)
        if value is None:
            continue
        try:
            setattr(settings, attr, value)
        except TypeError:
            pass

    ffmpeg = render.ffmpeg
    for attr, key in (
        ("format", "ffmpeg_format"),
        ("codec", "ffmpeg_codec"),
        ("constant_rate_factor", "constant_rate_factor"),
        ("ffmpeg_preset", "ffmpeg_preset"),
        ("use_autosplit", "use_autosplit"),
    ):
        value = settings_snapshot.get(key)
        if value is None:
            continue
        try:
            setattr(ffmpeg, attr, value)
        except TypeError:
            pass


def _store_viewport_state(space_data):
    overlay = space_data.overlay
    return {
        "shading_type": space_data.shading.type,
        "light": getattr(space_data.shading, "light", None),
        "show_cavity": getattr(space_data.shading, "show_cavity", None),
        "cavity_type": getattr(space_data.shading, "cavity_type", None),
        "cavity_ridge_factor": getattr(space_data.shading, "cavity_ridge_factor", None),
        "cavity_valley_factor": getattr(space_data.shading, "cavity_valley_factor", None),
        "use_scene_lights": getattr(space_data.shading, "use_scene_lights", None),
        "use_scene_world": getattr(space_data.shading, "use_scene_world", None),
        "render_pass": getattr(space_data.shading, "render_pass", None),
        "show_overlays": getattr(overlay, "show_overlays", None),
        "show_gizmo": getattr(space_data, "show_gizmo", None),
        "show_gizmo_navigate": getattr(space_data, "show_gizmo_navigate", None),
        "view_perspective": space_data.region_3d.view_perspective if space_data.region_3d else None,
    }


def _restore_viewport_state(space_data, state):
    overlay = space_data.overlay
    for attr, key in (
        ("type", "shading_type"),
        ("light", "light"),
        ("show_cavity", "show_cavity"),
        ("cavity_type", "cavity_type"),
        ("cavity_ridge_factor", "cavity_ridge_factor"),
        ("cavity_valley_factor", "cavity_valley_factor"),
        ("use_scene_lights", "use_scene_lights"),
        ("use_scene_world", "use_scene_world"),
        ("render_pass", "render_pass"),
    ):
        value = state.get(key)
        if value is not None and hasattr(space_data.shading, attr):
            try:
                setattr(space_data.shading, attr, value)
            except Exception:
                pass
    if state.get("show_overlays") is not None and hasattr(overlay, "show_overlays"):
        overlay.show_overlays = state["show_overlays"]
    if state.get("show_gizmo") is not None and hasattr(space_data, "show_gizmo"):
        space_data.show_gizmo = state["show_gizmo"]
    if state.get("show_gizmo_navigate") is not None and hasattr(space_data, "show_gizmo_navigate"):
        space_data.show_gizmo_navigate = state["show_gizmo_navigate"]
    if state.get("view_perspective") is not None and space_data.region_3d:
        space_data.region_3d.view_perspective = state["view_perspective"]


def _configure_omni_viewport(space_data, source_mode: str):
    overlay = space_data.overlay
    if source_mode == 'WORKBENCH':
        space_data.shading.type = 'SOLID'
        if hasattr(space_data.shading, "light"):
            space_data.shading.light = 'MATCAP'
        if hasattr(space_data.shading, "show_cavity"):
            space_data.shading.show_cavity = True
        if hasattr(space_data.shading, "cavity_type"):
            space_data.shading.cavity_type = 'WORLD'
        if hasattr(space_data.shading, "cavity_ridge_factor"):
            space_data.shading.cavity_ridge_factor = 2.5
        if hasattr(space_data.shading, "cavity_valley_factor"):
            space_data.shading.cavity_valley_factor = 1.0
    else:
        space_data.shading.type = 'MATERIAL'
        if hasattr(space_data.shading, "use_scene_lights"):
            space_data.shading.use_scene_lights = True
        if hasattr(space_data.shading, "use_scene_world"):
            space_data.shading.use_scene_world = True
        if hasattr(space_data.shading, "render_pass"):
            space_data.shading.render_pass = 'COMBINED'

    if hasattr(overlay, "show_overlays"):
        overlay.show_overlays = False
    if hasattr(space_data, "show_gizmo"):
        space_data.show_gizmo = False
    if hasattr(space_data, "show_gizmo_navigate"):
        space_data.show_gizmo_navigate = False
    if space_data.region_3d:
        space_data.region_3d.view_perspective = 'CAMERA'


def _configure_omni_scene(scene, source_mode: str, width: int, height: int, output_path: str):
    from . import texture_pipeline as pipe

    render = scene.render
    settings = render.image_settings
    if hasattr(settings, "media_type"):
        settings.media_type = 'IMAGE'

    if source_mode == 'WORKBENCH':
        pipe.setup_flat_render(scene, max(width, height))
    else:
        for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
            try:
                scene.render.engine = engine
                break
            except TypeError:
                continue

    render.resolution_x = width
    render.resolution_y = height
    render.resolution_percentage = 100
    render.filepath = output_path
    settings.file_format = 'PNG'
    settings.color_mode = 'RGB'
    settings.color_depth = '8'


def _configure_omni_video_scene(scene, source_mode: str, width: int, height: int, output_path: str):
    _configure_omni_scene(scene, source_mode, width, height, output_path)

    settings = scene.render.image_settings
    if hasattr(settings, "media_type"):
        settings.media_type = 'VIDEO'
    else:
        settings.file_format = 'FFMPEG'
    settings.color_mode = 'RGB'

    ffmpeg = scene.render.ffmpeg
    ffmpeg.format = 'MPEG4'
    ffmpeg.codec = 'H264'
    ffmpeg.constant_rate_factor = 'MEDIUM'
    ffmpeg.ffmpeg_preset = 'GOOD'
    ffmpeg.use_autosplit = False


def _capture_omni_still(scene, source_mode: str, aspect_ratio: str) -> dict:
    from . import texture_pipeline as pipe

    temp_dir = tempfile.mkdtemp(prefix="nanode_omni_frame_")
    output_path = os.path.join(temp_dir, "source.png")
    width, height = _capture_dimensions(scene, aspect_ratio=aspect_ratio)
    snap = pipe._store_render_settings(scene)
    output_snap = _store_omni_output_settings(scene)
    override = _get_viewport_context(scene)
    space_data = override["space_data"]
    viewport_state = _store_viewport_state(space_data)

    try:
        _configure_omni_scene(scene, source_mode, width, height, output_path)
        _configure_omni_viewport(space_data, source_mode)
        with bpy.context.temp_override(**override):
            bpy.ops.render.opengl(write_still=True)
        if not os.path.exists(output_path):
            raise RuntimeError("Omni source frame was not created")
        return {
            "path": output_path,
            "reference_paths": [],
            "media_type": "image",
            "source_mode": source_mode,
            "input_mode": "FRAME",
            "temp_dir": temp_dir,
        }
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    finally:
        _restore_viewport_state(space_data, viewport_state)
        _restore_omni_output_settings(scene, output_snap)
        pipe._restore_render_settings(scene, snap)


def _find_video_output(temp_dir: str, output_path: str) -> str:
    if os.path.exists(output_path):
        return output_path
    for name in os.listdir(temp_dir):
        if name.lower().endswith((".mp4", ".mov", ".mkv")):
            return os.path.join(temp_dir, name)
    raise RuntimeError("Omni source video was not created")


def _persist_omni_source_video(source_path: str) -> str:
    output_dir = os.path.join(tempfile.gettempdir(), "nanode_blender", "omni_captures")
    os.makedirs(output_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _, ext = os.path.splitext(source_path)
    if not ext:
        ext = ".mp4"
    output_path = os.path.join(output_dir, f"nanode_omni_source_{stamp}{ext.lower()}")
    shutil.copy2(source_path, output_path)
    return output_path


def _persist_omni_result(video_bytes: bytes) -> str:
    output_dir = os.path.join(tempfile.gettempdir(), "nanode_blender", "videos")
    os.makedirs(output_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = os.path.join(output_dir, f"nanode_omni_personal_{stamp}.mp4")
    with open(output_path, "wb") as output_file:
        output_file.write(video_bytes)
    return output_path


def _schedule_local_omni_result(
    scene_name: str,
    video_path: str,
    interaction_id: str,
    history_job: dict,
) -> None:
    def _load_result():
        scene = bpy.data.scenes.get(scene_name)
        if not scene:
            return None
        try:
            from .video_director import load_video_path_to_sequencer, record_video_job

            load_video_path_to_sequencer(video_path, int(history_job["id"]), "Omni Personal", scene_name)
            record_video_job(scene, history_job, source="OMNI_ENGINE", filepath=video_path)
            suffix = f" ({interaction_id})" if interaction_id else ""
            _set_omni_status(scene, f"Omni video loaded in Blender{suffix}")
        except Exception as exc:
            _set_omni_status(scene, f"Omni video ready, load failed: {exc}")
        return None

    bpy.app.timers.register(_load_result, first_interval=0.2)


def _capture_omni_video(scene, source_mode: str, duration_seconds: int, aspect_ratio: str) -> dict:
    from . import texture_pipeline as pipe

    temp_dir = tempfile.mkdtemp(prefix="nanode_omni_video_")
    output_path = os.path.join(temp_dir, "source.mp4")
    width, height = _capture_video_dimensions(scene, aspect_ratio=aspect_ratio)
    snap = pipe._store_render_settings(scene)
    output_snap = _store_omni_output_settings(scene)
    frame_current = scene.frame_current
    frame_start = scene.frame_start
    frame_end = scene.frame_end
    override = _get_viewport_context(scene)
    space_data = override["space_data"]
    viewport_state = _store_viewport_state(space_data)

    try:
        _configure_omni_video_scene(scene, source_mode, width, height, output_path)
        _configure_omni_viewport(space_data, source_mode)

        frame_count = _duration_frame_count(scene, duration_seconds)
        scene.frame_start = frame_current
        scene.frame_end = frame_current + frame_count - 1

        with bpy.context.temp_override(**override):
            bpy.ops.render.opengl(animation=True)

        source_path = _find_video_output(temp_dir, output_path)
        debug_path = ""
        try:
            debug_path = _persist_omni_source_video(source_path)
            print(f"[NANODE OMNI] Source video saved for inspection: {debug_path}")
        except Exception as exc:
            print(f"[NANODE OMNI] Could not save inspection copy: {exc}")

        return {
            "path": source_path,
            "debug_path": debug_path,
            "reference_paths": [],
            "media_type": "video",
            "source_mode": source_mode,
            "input_mode": "VIDEO_EDIT",
            "temp_dir": temp_dir,
        }
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    finally:
        _restore_viewport_state(space_data, viewport_state)
        scene.frame_start = frame_start
        scene.frame_end = frame_end
        scene.frame_set(frame_current)
        _restore_omni_output_settings(scene, output_snap)
        pipe._restore_render_settings(scene, snap)


def _capture_omni_timeline_frames(
    scene,
    source_mode: str,
    duration_seconds: int,
    aspect_ratio: str,
) -> dict:
    from . import texture_pipeline as pipe

    temp_dir = tempfile.mkdtemp(prefix="nanode_omni_frames_")
    width, height = _capture_dimensions(scene, aspect_ratio=aspect_ratio)
    snap = pipe._store_render_settings(scene)
    output_snap = _store_omni_output_settings(scene)
    original_frame = scene.frame_current
    override = _get_viewport_context(scene)
    space_data = override["space_data"]
    viewport_state = _store_viewport_state(space_data)

    start_frame = original_frame
    if start_frame >= scene.frame_end:
        start_frame = scene.frame_start
    duration_end = start_frame + _duration_frame_count(scene, duration_seconds) - 1
    end_frame = max(start_frame, min(scene.frame_end, duration_end))
    middle_frame = int(round((start_frame + end_frame) / 2))
    sample_frames = (start_frame, middle_frame, end_frame)
    paths = []

    try:
        first_output = os.path.join(temp_dir, "frame_01.png")
        _configure_omni_scene(scene, source_mode, width, height, first_output)
        _configure_omni_viewport(space_data, source_mode)

        with bpy.context.temp_override(**override):
            for index, frame in enumerate(sample_frames, start=1):
                output_path = os.path.join(temp_dir, f"frame_{index:02d}.png")
                scene.frame_set(frame)
                scene.render.filepath = output_path
                bpy.ops.render.opengl(write_still=True)
                if not os.path.isfile(output_path):
                    raise RuntimeError(f"Omni guide frame {index} was not created")
                paths.append(output_path)

        return {
            "path": paths[0],
            "reference_paths": paths[1:],
            "media_type": "image_sequence",
            "source_mode": source_mode,
            "input_mode": "TIMELINE_FRAMES",
            "temp_dir": temp_dir,
        }
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    finally:
        _restore_viewport_state(space_data, viewport_state)
        scene.frame_set(original_frame)
        _restore_omni_output_settings(scene, output_snap)
        pipe._restore_render_settings(scene, snap)


def _prepare_omni_capture(scene, props) -> dict:
    source_mode = getattr(props, "omni_render_mode", "WORKBENCH")
    input_mode = getattr(props, "omni_input_mode", "TIMELINE_FRAMES")
    duration = int(getattr(props, "omni_duration", "") or "10")
    aspect_ratio = _normalize_video_aspect_ratio(getattr(props, "omni_aspect_ratio", "16:9"))
    apply_omni_camera_aspect(scene, aspect_ratio)
    reused_source = bpy.path.abspath(getattr(props, "omni_source_video_override", "") or "")

    if reused_source:
        if not os.path.isfile(reused_source):
            raise RuntimeError("Reused Omni motion guide is missing; clear it or choose another history item")
        capture = {
            "path": reused_source,
            "debug_path": reused_source,
            "reference_paths": [],
            "media_type": "video",
            "source_mode": source_mode,
            "input_mode": "VIDEO_EDIT",
            "temp_dir": tempfile.mkdtemp(prefix="nanode_omni_reuse_"),
        }
    elif input_mode == 'VIDEO_EDIT' and scene.frame_end > scene.frame_start:
        capture = _capture_omni_video(scene, source_mode, duration, aspect_ratio)
    elif input_mode == 'TIMELINE_FRAMES' and scene.frame_end > scene.frame_start:
        capture = _capture_omni_timeline_frames(scene, source_mode, duration, aspect_ratio)
    else:
        capture = _capture_omni_still(scene, source_mode, aspect_ratio)

    if props.use_style_reference and props.style_reference_image:
        from .video_director import _export_image

        references = list(capture.get("reference_paths") or [])
        capture["style_reference_index"] = len(references)
        references.append(
            _export_image(
                props.style_reference_image,
                capture["temp_dir"],
                "omni_style_reference.png",
            )
        )
        capture["reference_paths"] = references
    return capture


def _build_omni_prompt(
    user_prompt: str,
    source_mode: str,
    media_type: str,
    style_reference_index: int | None = None,
) -> str:
    style_brief = (user_prompt or "").strip()
    style_brief = re.sub(r"\b[Ss]hots\b", "views", style_brief)
    style_brief = re.sub(r"\b[Ss]hot\b", "view", style_brief)
    if not style_brief:
        style_brief = "polished cinematic 3D render"

    subject_lock = (
        "Treat every foreground character and primary subject as identity-locked. "
        "Preserve the exact face, body proportions, hairstyle, clothing, footwear, accessories, "
        "held objects, colors, silhouette, and visible construction from the source. "
        "Do not add, remove, replace, or redesign any character detail, including capes, coats, "
        "armor, jewelry, bags, hats, or props. Improve only the rendering of existing details. "
        "Background lighting and non-subject environment detail may be enriched, but new background "
        "elements must not touch, cover, alter, or visually merge with a foreground subject. "
    )

    style_directive = ""
    image_number = 0
    if style_reference_index is not None:
        image_number = style_reference_index + (1 if media_type == "video" else 2)
        style_directive = (
            f"[# References <IMAGE_REF_{style_reference_index}>@Image{image_number}] "
        )

    if media_type == "video":
        base_prompt = (
            f"{style_directive}"
            "Re-render this rough 3D animation as a finished 3D render. "
            "Keep the same camera, timing, objects, positions, scale, silhouettes, and scene layout. "
            "Improve lighting, materials, textures, shading, color grading, and render quality. "
            f"{subject_lock}"
            "Keep everything else the same. "
            f"Requested result: {style_brief}"
        )
        source_label = "the rough source animation"
        preserve_fields = [
            "duration",
            "timing",
            "camera_path",
            "object_motion",
            "object_identity",
            "character_identity",
            "face",
            "body_proportions",
            "wardrobe",
            "accessories",
            "object_positions",
            "geometry",
            "composition",
            "framing",
        ]
    elif media_type == "image_sequence":
        base_prompt = (
            "[# Sources <FIRST_FRAME>@Image1] "
            "[# References <IMAGE_REF_0>@Image2 <IMAGE_REF_1>@Image3] "
            f"{style_directive}"
            "Create a single continuous finished 3D animation from these rough 3D guide frames. "
            "Use Image1 as the starting frame. Images 2 and 3 are chronological motion, pose, and camera guides. "
            "Preserve the same geometry, object identity, camera path, composition, timing, scale, and silhouettes. "
            "Replace viewport shading with finished lighting, materials, textures, shadows, reflections, and color grading. "
            f"{subject_lock}"
            "No scene cuts. Keep everything else the same. "
            f"Requested result: {style_brief}"
        )
        source_label = "the chronological Blender guide frames"
        preserve_fields = [
            "timing",
            "camera_path",
            "pose_progression",
            "object_identity",
            "character_identity",
            "face",
            "body_proportions",
            "wardrobe",
            "accessories",
            "geometry",
            "composition",
            "scale",
            "silhouettes",
        ]
    else:
        base_prompt = (
            f"{style_directive}"
            "<FIRST_FRAME> Create a single continuous finished 3D animation from this rough 3D guide frame. "
            "Use this image as the starting frame. Preserve the same camera framing, geometry, objects, scale, silhouettes, and layout. "
            "Add natural motion described by the user and finished lighting, materials, textures, shadows, reflections, and color grading. "
            f"{subject_lock}"
            "No scene cuts. Keep everything else the same. "
            f"Requested result: {style_brief}"
        )
        source_label = "the rough Blender guide frame"
        preserve_fields = [
            "camera_framing",
            "object_identity",
            "character_identity",
            "face",
            "body_proportions",
            "wardrobe",
            "accessories",
            "object_positions",
            "geometry",
            "composition",
            "scale",
            "silhouettes",
            "scene_layout",
        ]

    if style_reference_index is None:
        return base_prompt
    from . import gemini_api

    return gemini_api.append_style_reference_policy(
        base_prompt,
        reference_label=f"Image{image_number}",
        source_label=source_label,
        preserve_fields=preserve_fields,
    )


def _cleanup_capture():
    temp_dir = _pre_capture.get("temp_dir")
    if temp_dir:
        shutil.rmtree(temp_dir, ignore_errors=True)
    _pre_capture['path'] = None
    _pre_capture['ready'] = False
    _pre_capture['engine'] = None
    _pre_capture['reference_paths'] = []
    _pre_capture['style_reference_index'] = None
    _pre_capture['temp_dir'] = None
    _pre_capture['debug_path'] = None
    _pre_capture['request_id'] = None


def reset_runtime_state():
    global _omni_runtime_generation, _omni_autotrigger_pending
    _omni_runtime_generation += 1
    _omni_polling_job_ids.clear()
    _omni_autotrigger_pending = False
    _finish_omni_submission(apply_cooldown=False)
    _cleanup_capture()


class NanodeOmniRenderEngine(bpy.types.RenderEngine):
    """Omni video engine that turns rough Blender motion into a Nanode video job."""
    bl_idname = 'NANODE_OMNI'
    bl_label = 'Omni Engine'
    bl_use_preview = False
    bl_use_shading_nodes_custom = False
    bl_use_eevee_viewport = True
    bl_use_gpu_context = False

    def render(self, depsgraph):
        global _omni_autotrigger_pending
        scene = depsgraph.scene
        props = scene.gemini_render if hasattr(scene, 'gemini_render') else None

        if self.is_preview:
            return

        if not props:
            self.report({'ERROR'}, "Nanode properties not found")
            return

        if self.is_animation:
            message = "Render Animation is disabled for Omni Engine. Use Render Omni Video once."
            live_scene = bpy.data.scenes.get(scene.name)
            if live_scene and hasattr(live_scene, "gemini_render"):
                live_scene.gemini_render.omni_status = message
            _cleanup_capture()
            _finish_omni_submission()
            self.report({'ERROR'}, message)
            raise RuntimeError(message)

        if not _pre_capture.get('ready') or not _pre_capture.get('path') or _pre_capture.get('engine') != 'NANODE_OMNI':
            render_w = int(scene.render.resolution_x * scene.render.resolution_percentage / 100)
            render_h = int(scene.render.resolution_y * scene.render.resolution_percentage / 100)
            result = self.begin_result(0, 0, render_w, render_h)
            self.end_result(result)

            if _omni_autotrigger_pending or _omni_submission_active:
                return

            _omni_autotrigger_pending = True

            def _trigger_proper_render():
                global _omni_autotrigger_pending
                _omni_autotrigger_pending = False
                try:
                    if not _omni_submission_active:
                        bpy.ops.banana.ai_render()
                except Exception as e:
                    print(f"[NANODE OMNI] Auto-trigger failed: {e}")
                return None

            bpy.app.timers.register(_trigger_proper_render, first_interval=0.5)
            return

        capture_path = _pre_capture['path']
        debug_path = _pre_capture.get('debug_path') or ""
        reference_paths = list(_pre_capture.get('reference_paths') or [])
        style_reference_index = _pre_capture.get('style_reference_index')
        media_type = _pre_capture.get('media_type', 'image')
        source_mode = _pre_capture.get('source_mode', 'WORKBENCH')
        request_id = _pre_capture.get('request_id') or uuid.uuid4().hex
        duration = int(getattr(props, "omni_duration", "") or "10")
        task = 'edit' if media_type == 'video' else ('auto' if media_type == 'image_sequence' else 'image_to_video')
        match_source_duration = media_type == 'video'
        if match_source_duration:
            try:
                from . import video_director

                duration = video_director._nearest_omni_duration(
                    video_director._probe_video_duration_seconds(capture_path)
                )
            except Exception as exc:
                print(f"[NANODE OMNI] Could not detect source duration; using {duration}s for pricing: {exc}")

        from . import beta_api, gemini_api

        try:
            prefs = bpy.context.preferences.addons.get("nano_banana_render")
            token = prefs.preferences.beta_token.strip() if prefs else ""
            omni_prompt = _build_omni_prompt(
                props.prompt,
                source_mode,
                media_type,
                style_reference_index,
            )
            aspect_ratio = _normalize_video_aspect_ratio(getattr(props, "omni_aspect_ratio", "16:9"))

            if auth_utils.is_google_api_key(token):
                self.update_stats("", "Generating Omni video with personal Google API...")
                _set_omni_status(scene, "Generating with personal Google API...", output_url="")
                video_bytes, interaction_id = gemini_api.generate_omni_video_direct(
                    api_key=token,
                    prompt=omni_prompt,
                    task=task,
                    duration_seconds=duration,
                    aspect_ratio=aspect_ratio,
                    input_image_path=capture_path if media_type != 'video' else None,
                    reference_image_paths=reference_paths,
                    video_path=capture_path if media_type == 'video' else None,
                    match_source_duration=match_source_duration,
                )
                output_path = _persist_omni_result(video_bytes)
                local_job = {
                    "entry_id": f"local:{int(time.time() * 1000)}",
                    "id": int(time.time()),
                    "model": "gemini-omni-flash-preview",
                    "task": task,
                    "status": "succeeded",
                    "duration_seconds": duration,
                    "resolution": "720p",
                    "aspect_ratio": aspect_ratio,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "user_prompt": props.prompt,
                    "source_video_path": debug_path,
                    "style_reference_name": (
                        props.style_reference_image.name
                        if props.use_style_reference and props.style_reference_image
                        else ""
                    ),
                }
                _schedule_local_omni_result(scene.name, output_path, interaction_id, local_job)
                _set_omni_status(scene, "Omni video ready; loading preview...")
                self.update_stats("", "Omni video generated")
            else:
                self.update_stats("", "Queueing Omni video job...")
                _set_omni_status(scene, "Queueing Omni video...", output_url="")
                response = beta_api.create_video_job(
                    prompt=omni_prompt,
                    model="gemini-omni-flash-preview",
                    task=task,
                    duration_seconds=duration,
                    resolution="720p",
                    aspect_ratio=aspect_ratio,
                    input_image_path=capture_path if media_type != 'video' else None,
                    reference_image_paths=reference_paths,
                    video_path=capture_path if media_type == 'video' else None,
                    request_id=request_id,
                    match_source_duration=match_source_duration,
                )
                job = response.get("job", response)
                job["user_prompt"] = props.prompt
                job["source_video_path"] = debug_path
                job["style_reference_name"] = (
                    props.style_reference_image.name
                    if props.use_style_reference and props.style_reference_image
                    else ""
                )
                job_id = int(job.get("id") or 0)
                credit_cost = int(job.get("credit_cost") or 0)
                status = f"Omni job queued ({credit_cost} credits)"
                if debug_path:
                    status = f"{status}. Source saved: {debug_path}"
                _set_omni_status(scene, status, job_id, job.get("output_url") or "")
                from .video_director import record_video_job

                record_video_job(scene, job, source="OMNI_ENGINE")
                _schedule_omni_job_poll(scene.name, job_id)
                if "balance" in response:
                    props.beta_balance = int(response.get("balance") or 0)
                self.update_stats("", f"Omni job #{job_id} queued")

            render_w = int(scene.render.resolution_x * scene.render.resolution_percentage / 100)
            render_h = int(scene.render.resolution_y * scene.render.resolution_percentage / 100)
            if media_type != 'video':
                with open(capture_path, "rb") as file:
                    image_data = file.read()
                self._write_image_to_render_buffer(image_data, render_w, render_h)
            else:
                result = self.begin_result(0, 0, render_w, render_h)
                self.end_result(result)

        except beta_api.BetaAPIError as exc:
            if beta_api.is_invalid_token_error(exc):
                message = "Nanode login expired. Log in with Google again."
            else:
                message = f"Omni server error: {exc.message}"
            _set_omni_status(scene, message)
            self.report({'ERROR'}, message)
        except Exception as exc:
            _set_omni_status(scene, f"Omni failed: {exc}")
            self.report({'ERROR'}, f"Omni failed: {exc}")
        finally:
            _cleanup_capture()
            _finish_omni_submission()

    def _write_image_to_render_buffer(self, image_data: bytes, render_w: int, render_h: int):
        return NanoBananaRenderEngine._write_image_to_render_buffer(self, image_data, render_w, render_h)


def _finalize_render_in_main_thread(image_data: bytes, prompt: str, scene, elapsed: float):
    """Helper executed in main thread to load image datablock and swap viewer."""
    import tempfile
    import os
    temp_path = None
    
    try:
        _save_render_to_history(image_data, prompt, scene)
    except Exception as e:
        print(f"[NANO BANANA] History save error: {e}")
        
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(image_data)
            temp_path = f.name

        result_img_name = "Nano Banana Render"
        if result_img_name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[result_img_name])

        result_img = bpy.data.images.load(temp_path)
        result_img.name = result_img_name
        result_img.colorspace_settings.name = 'sRGB'
        result_img.pack()

        _pre_capture['result_image'] = result_img_name
    except Exception as e:
        print(f"[NANO BANANA] Error loading AI result into Blender: {e}")
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    if hasattr(scene, 'gemini_render'):
        scene.gemini_render.status_text = f"Done in {elapsed:.1f}s"
        scene.gemini_render.is_rendering = False

    result_img_name = _pre_capture.get('result_image')
    if result_img_name and result_img_name in bpy.data.images:
        ai_img = bpy.data.images[result_img_name]
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    for space in area.spaces:
                        if space.type == 'IMAGE_EDITOR' and getattr(space.image, 'name', '') == 'Render Result':
                            space.image = ai_img
                area.tag_redraw()


def _save_render_to_history(image_data: bytes, user_prompt: str, scene):
    """Save render result to history with packed image data."""
    import tempfile
    import datetime
    import shutil

    if not user_prompt:
        return

    timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    permanent_name = f"AI_Result_{timestamp_str}"

    # Save to permanent location
    permanent_dir = os.path.join(tempfile.gettempdir(), "nano_banana_history")
    os.makedirs(permanent_dir, exist_ok=True)
    permanent_path = os.path.join(permanent_dir, f"{permanent_name}.png")

    with open(permanent_path, 'wb') as f:
        f.write(image_data)

    # Load and pack
    if permanent_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[permanent_name])

    img = bpy.data.images.load(permanent_path)
    img.name = permanent_name
    img.pack()
    img.use_fake_user = True
    print(f"[NANO BANANA] History image packed: {permanent_name}")

    # Add to history
    if hasattr(scene, 'gemini_render'):
        props = scene.gemini_render
        history_item = props.render_history.add()
        history_item.prompt = user_prompt
        history_item.image_name = permanent_name

        if props.use_style_reference and props.style_reference_image:
            history_item.style_reference_used = True
            history_item.style_reference_name = props.style_reference_image.name
        else:
            history_item.style_reference_used = False

        history_item.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_item.thumbnail_name = ""

        while len(props.render_history) > 10:
            oldest = props.render_history[0]
            if oldest.image_name in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[oldest.image_name])
            props.render_history.remove(0)

        print(f"[NANO BANANA] History saved: {permanent_name}, total: {len(props.render_history)}")


# --- Standard Blender Panels ---
# These are standard panels (Output, Scene, View Layer, etc.) that need
# our engine added to their COMPAT_ENGINES to appear when Nano Banana is selected.

def get_standard_panels():
    """Find standard Blender panels that should be visible with our engine."""
    exclude_panels = {
        # Exclude render-specific panels we don't need (these clutter the UI)
        'RENDER_PT_simplify',
        'RENDER_PT_freestyle',
        'RENDER_PT_color_management_display_settings',
    }

    panels = []
    for attr_name in dir(bpy.types):
        panel = getattr(bpy.types, attr_name, None)
        if panel is None:
            continue
        if not hasattr(panel, 'COMPAT_ENGINES'):
            continue
        if not hasattr(panel, 'bl_context'):
            continue

        # Include panels from all standard Blender tabs EXCEPT the Render tab
        # (Nano Banana provides its own UI for the Render tab)
        bl_context = getattr(panel, 'bl_context', '')
        if bl_context != 'render':
            if hasattr(panel, 'bl_idname') and panel.bl_idname in exclude_panels:
                continue
            # Only include panels that already work with EEVEE
            if 'BLENDER_EEVEE' in panel.COMPAT_ENGINES or 'BLENDER_EEVEE_NEXT' in panel.COMPAT_ENGINES:
                panels.append(panel)

    return panels


# --- Keymap ---
addon_keymaps = []
_registered_panels = []

# Track previous engine to detect switch
_last_engine = [None]


def _on_engine_switch(scene):
    """Initialize viewport when user first switches to Nano Banana engine.
    Sets the viewport shading to match the current render_mode so the
    viewport is never blank on first selection."""
    try:
        props = scene.gemini_render if hasattr(scene, 'gemini_render') else None
        if not props:
            return

        if props.render_mode == 'EEVEE':
            # Regular Render — show Material Preview with Combined pass
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                space.shading.type = 'MATERIAL'
                                if hasattr(space.shading, 'render_pass'):
                                    space.shading.render_pass = 'COMBINED'
                                if hasattr(space.shading, 'use_scene_lights'):
                                    space.shading.use_scene_lights = True
                        area.tag_redraw()
                        return
        else:
            # Depth Map — show Material Preview with Mist pass
            from . import ui_panel
            ui_panel.on_render_mode_change(props, bpy.context)
    except Exception as e:
        print(f"[NANO BANANA] Engine switch viewport init error: {e}")


@bpy.app.handlers.persistent
def _depsgraph_update_handler(scene, depsgraph=None):
    """Detect when render engine changes to NANO_BANANA and initialise viewport."""
    try:
        current = scene.render.engine
        if current != _last_engine[0]:
            prev = _last_engine[0]
            _last_engine[0] = current
            if current == 'NANO_BANANA' and prev is not None:
                # User just switched to our engine — set up viewport
                _on_engine_switch(scene)
            elif current == 'NANODE_OMNI':
                props = getattr(scene, "gemini_render", None)
                aspect_ratio = getattr(props, "omni_aspect_ratio", "16:9") if props else "16:9"
                apply_omni_camera_aspect(scene, aspect_ratio)
    except Exception:
        pass


def register():
    bpy.utils.register_class(NanoBananaRenderEngine)
    bpy.utils.register_class(NanodeOmniRenderEngine)
    bpy.utils.register_class(BananaOTRender)

    # Add our engine to standard Blender panels
    for panel in get_standard_panels():
        if hasattr(panel, 'COMPAT_ENGINES'):
            panel.COMPAT_ENGINES.add('NANO_BANANA')
            panel.COMPAT_ENGINES.add('NANODE_OMNI')
            _registered_panels.append(panel)

    # Register F12 keymap override
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Screen', space_type='EMPTY')
        kmi = km.keymap_items.new("banana.ai_render", 'F12', 'PRESS')
        addon_keymaps.append((km, kmi))

    # Register engine-switch handler
    if _depsgraph_update_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_depsgraph_update_handler)
    # Seed current engine so we don't trigger on addon load
    try:
        _last_engine[0] = bpy.context.scene.render.engine
    except Exception:
        _last_engine[0] = None


def unregister():
    reset_runtime_state()
    # Remove engine-switch handler
    if _depsgraph_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_depsgraph_update_handler)

    # Remove keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Remove our engine from standard panels
    for panel in _registered_panels:
        if hasattr(panel, 'COMPAT_ENGINES'):
            panel.COMPAT_ENGINES.discard('NANO_BANANA')
            panel.COMPAT_ENGINES.discard('NANODE_OMNI')
    _registered_panels.clear()

    bpy.utils.unregister_class(BananaOTRender)
    bpy.utils.unregister_class(NanodeOmniRenderEngine)
    bpy.utils.unregister_class(NanoBananaRenderEngine)
