import os

import bpy

OP_RATE_GEN = "banana.rate_generation"
OP_TOGGLE_FEEDBACK = "banana.toggle_feedback"
from typing import Callable, Any, Optional
from bpy.types import PropertyGroup, Panel
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, IntProperty, CollectionProperty, PointerProperty
from .model_config import (
    IMAGE_MODEL_ITEMS,
    OMNI_DURATION_ITEMS,
    VIDEO_ASPECT_ITEMS,
    get_image_cost,
    get_omni_cost,
    supports_image_resolution,
)
from . import auth_utils


def on_omni_aspect_ratio_change(props, context) -> None:
    scene = getattr(context, "scene", None)
    if not scene:
        return
    from . import render_engine

    render_engine.apply_omni_camera_aspect(scene, props.omni_aspect_ratio)


class GeminiRenderHistoryItem(PropertyGroup):
    """Single render history entry with visual preview"""
    
    prompt: StringProperty(
        name="Prompt",
        description="Prompt used for this render",
        default=""
    )
    
    timestamp: StringProperty(
        name="Timestamp", 
        description="When this render was created",
        default=""
    )
    
    filepath: StringProperty(
        name="File Path",
        description="Path to the saved image file for preview",
        default=""
    )
    
    image_name: StringProperty(
        name="Image Name",
        description="Name of the generated image in Blender",
        default=""
    )
    
    # Visual preview data
    thumbnail_name: StringProperty(
        name="Thumbnail Name",
        description="Name of thumbnail image in bpy.data.images",
        default=""
    )
    
    # Style reference data
    style_reference_used: BoolProperty(
        name="Style Reference Used",
        description="Whether style reference was used for this render",
        default=False
    )
    
    style_reference_name: StringProperty(
        name="Style Reference Name",
        description="Name of style reference image used",
        default=""
    )
    
    style_reference_thumbnail: StringProperty(
        name="Style Reference Thumbnail",
        description="Name of style reference thumbnail in bpy.data.images",
        default=""
    )

class GeminiRenderProperties(PropertyGroup):
    """Properties for Gemini Render addon stored in scene"""
    
    # AI Model selection (shown like Device selector in Cycles)
    ai_model: EnumProperty(
        name="Model",
        description="Select which AI model to use for rendering",
        items=[
            ('NANO_BANANA_2_LITE', "Nano Banana 2 Lite", "gemini-3.1-flash-lite-image - fastest, 1K only"),
            ('NANO_BANANA_2', "Nano Banana 2", "gemini-3.1-flash-image - Fast, balanced quality"),
            ('NANO_BANANA_PRO', "Nano Banana Pro", "gemini-3-pro-image - Highest quality, slower"),
            ('NANO_BANANA', "Nano Banana", "gemini-2.5-flash-image — Basic, fastest"),
        ],
        default='NANO_BANANA_PRO',
    )
    
    prompt: StringProperty(
        name="Prompt", 
        description="Describe how you want the depth map to be transformed into a photorealistic render",
        default="Make this photorealistic with detailed materials and proper lighting",
        maxlen=1000,
    )
    
    # Render History
    render_history: CollectionProperty(
        type=GeminiRenderHistoryItem,
        name="Render History"
    )
    
    history_index: IntProperty(
        name="History Index",
        default=-1,
    )
    
    # Render mode selection
    render_mode: EnumProperty(
        name="Render Mode",
        description="Choose between depth map (mist) or regular Eevee render",
        items=[
            ('DEPTH', "Depth Map (Mist)", "Use mist pass for pure depth information — no textures/lighting needed"),
            ('EEVEE', "Regular Render", "Use standard Eevee render — preserves colors, textures, and lighting"),
        ],
        default='EEVEE',
        update=lambda self, context: on_render_mode_change(self, context)
    )
    
    # Resolution selection
    resolution: EnumProperty(
        name="Resolution",
        description="AI output resolution (aspect ratio auto-detected from scene/camera)",
        items=[
            ('1024', "1K", "Base 1024px (auto aspect ratio)"),
            ('2048', "2K", "High resolution 2048px"),
            ('4096', "4K", "Ultra high resolution 4096px"),
        ],
        default='1024',
    )
    
    # Mist Pass settings for depth rendering
    mist_start: FloatProperty(
        name="Start",
        description="Start distance for mist pass (objects closer than this are fully white)",
        default=5.0,
        min=0.01,
        max=1000.0,
        unit='LENGTH',
        update=lambda self, context: update_mist_settings(self, context)
    )
    
    mist_depth: FloatProperty(
        name="Depth", 
        description="Depth distance for mist pass (range over which mist fades from white to black)",
        default=25.0,
        min=0.1,
        max=1000.0,
        unit='LENGTH',
        update=lambda self, context: update_mist_settings(self, context)
    )
    
    mist_falloff: EnumProperty(
        name="Falloff",
        description="Mist falloff type — controls how depth gradient transitions",
        items=[
            ('LINEAR', "Linear", "Linear depth gradient — smooth and even transition"),
            ('QUADRATIC', "Quadratic", "Quadratic depth gradient — more contrast in middle range"),
            ('INVERSE_QUADRATIC', "Inverse Quadratic", "Inverse quadratic — stronger contrast at distance"),
        ],
        default='LINEAR',
        update=lambda self, context: update_mist_settings(self, context)
    )
    
    # Preview mist in viewport
    mist_preview: BoolProperty(
        name="Preview Mist",
        description="Show mist effect in 3D viewport for easy depth adjustment",
        default=False,
        update=lambda self, context: toggle_mist_preview(self, context)
    )
    
    # Style Reference Image
    use_style_reference: BoolProperty(
        name="Style Reference",
        description="Use a reference image to copy its style, materials, colors, and lighting to the render",
        default=False
    )
    
    style_reference_image: PointerProperty(
        type=bpy.types.Image,
        name="Reference",
        description="Reference image — AI will copy materials, colors, lighting, textures from this image while using depth map geometry"
    )
    
    # UI state
    show_settings: BoolProperty(
        name="Show Settings",
        description="Show advanced settings",
        default=False,
    )
    
    show_auth: BoolProperty(
        name="Show Authentication",
        description="Show authentication panel",
        default=True,
    )
    
    # Status
    status_text: StringProperty(
        name="Status",
        description="Current operation status",
        default="Ready",
    )
    
    is_rendering: BoolProperty(
        name="Is Rendering",
        description="Whether AI render is in progress",
        default=False,
    )

    # ─── Beta Properties ──────────────────────────────────────
    omni_render_mode: EnumProperty(
        name="Source Render",
        description="Render source that Omni uses as geometry, camera, and motion guidance",
        items=[
            ('WORKBENCH', "Workbench", "Flat Workbench/MatCap render using the same geometry settings as AI Texturing"),
            ('EEVEE', "Eevee", "Scene Eevee render with current materials, lights, and camera"),
        ],
        default='EEVEE',
    )

    omni_input_mode: EnumProperty(
        name="Input",
        description="Choose how Blender animation guides Omni",
        items=[
            ('TIMELINE_FRAMES', "Timeline Frames", "Use the first, middle, and last blocking frames as motion guidance"),
            ('FRAME', "Current Frame", "Animate the current camera frame from the prompt"),
            ('VIDEO_EDIT', "Uploaded Motion Guide", "Upload the viewport animation for Omni rendering"),
        ],
        default='VIDEO_EDIT',
    )

    omni_duration: EnumProperty(
        name="Duration",
        description="Video duration",
        items=OMNI_DURATION_ITEMS,
        default='10',
    )

    omni_aspect_ratio: EnumProperty(
        name="Aspect",
        description="Omni output aspect ratio",
        items=VIDEO_ASPECT_ITEMS,
        default='16:9',
        update=on_omni_aspect_ratio_change,
    )

    omni_status: StringProperty(
        name="Omni Status",
        description="Latest Omni video job status",
        default="",
    )

    omni_last_job_id: IntProperty(
        name="Omni Job ID",
        description="Last Omni video job ID",
        default=0,
    )

    omni_output_url: StringProperty(
        name="Omni Output URL",
        description="Latest Omni video result URL",
        default="",
    )

    omni_source_video_override: StringProperty(
        name="Reused Motion Guide",
        description="Previously captured viewport video reused for the next Omni render",
        default="",
        subtype='FILE_PATH',
    )

    beta_balance: IntProperty(
        name="Balance",
        description="Remaining AI generations",
        default=-1,
    )
    
    feedback_text: StringProperty(
        name="Feedback",
        description="Your feedback about the addon",
        default="",
        maxlen=500,
    )
    
    show_feedback: BoolProperty(
        name="Show Feedback",
        description="Toggle feedback input",
        default=False,
    )
    
    has_submitted_feedback: BoolProperty(
        name="Feedback Submitted",
        default=False,
    )
    
    tex_ui_show_cam_setup: BoolProperty(name="Camera Setup", default=True)
    tex_ui_show_depth_setup: BoolProperty(name="Depth Settings", default=True)
    
    last_generation_id: IntProperty(
        name="Last Generation ID",
        description="ID of the last generation for rating",
        default=0,
    )
    
    last_generation_rated: BoolProperty(
        name="Rated",
        description="Whether the last generation has been rated",
        default=True,
    )

    # ─── AI Texturing Properties ──────────────────────────────
    tex_render_mode: EnumProperty(
        name="Render Mode",
        description="Type of image to render for AI generation",
        items=[
            ('MIST', "Depth Map", "Render using distance-based mist"),
            ('COLOR', "Workbench", "Render using standard Workbench engine"),
        ],
        default='MIST',
        update=lambda self, ctx: on_tex_render_mode_change(self, ctx)
    )

    tex_prompt: StringProperty(
        name="Texture Prompt",
        description="Describe the desired surface material / texture style",
        default="Photorealistic PBR texture with detailed materials",
        maxlen=1000,
    )

    tex_reference_image: PointerProperty(
        name="Style Reference",
        description="Reference image whose visual style will guide AI texture generation",
        type=bpy.types.Image,
    )

    tex_resolution: EnumProperty(
        name="Projection Resolution",
        description="Resolution of each AI projection view (per camera angle). This is NOT the final texture resolution — the texture is composited from multiple projections",
        items=[
            ('1024', "1K", "1024×1024 per projection — fast, lower detail"),
            ('2048', "2K", "2048×2048 per projection — balanced"),
            ('4096', "4K", "4096×4096 per projection — highest projection detail"),
        ],
        default='1024',
    )

    tex_auto_uv: BoolProperty(
        name="Auto UV Unwrap",
        description="Automatically create a clean UV map (Smart UV Project). "
                    "Disable if you have a custom UV layout you want to keep",
        default=True,
    )

    tex_include_bottom: BoolProperty(
        name="Include Bottom",
        description="Add a bottom camera. Disable to save one API request "
                    "for models that don't need bottom textures",
        default=False,
    )

    tex_include_top: BoolProperty(
        name="Include Top",
        description="Add a top-down camera",
        default=True,
    )

    tex_camera_preset: EnumProperty(
        name="Camera Layout",
        description="Choose how cameras are arranged around the model",
        items=[
            ('CUBE',    "Cube (4+)",
             "4 side cameras (Front/Back/Left/Right) + optional Top/Bottom"),
            ('RING_8',  "Ring (8+)",
             "8 cameras evenly spaced around the model + optional Top/Bottom"),
            ('HEMI_10', "Hemisphere (10+)",
             "8 equator + 2 elevated cameras + optional Top/Bottom"),
        ],
        default='CUBE',
    )

    tex_cam_distance: FloatProperty(
        name="Camera Distance",
        description="Distance from cameras to model centre. 0 = auto-compute",
        default=0.0,
        min=0.0,
        max=500.0,
        unit='LENGTH',
        update=lambda self, ctx: on_cam_settings_change(self, ctx),
    )

    tex_cam_ortho_scale: FloatProperty(
        name="Ortho Scale",
        description="Orthographic scale for cameras. 0 = auto-compute from model size",
        default=0.0,
        min=0.0,
        max=500.0,
        update=lambda self, ctx: on_cam_settings_change(self, ctx),
    )

    # Depth settings for texture pipeline — update mist live
    tex_depth_start: FloatProperty(
        name="Depth Start",
        description="Mist start for texture depth maps",
        default=0.1,
        min=0.001,
        max=100.0,
        unit='LENGTH',
        update=lambda self, ctx: update_tex_mist_settings(self, ctx),
    )

    tex_depth_depth: FloatProperty(
        name="Depth Range",
        description="Mist depth range for texture depth maps",
        default=10.0,
        min=0.1,
        max=200.0,
        unit='LENGTH',
        update=lambda self, ctx: update_tex_mist_settings(self, ctx),
    )

    # Pipeline state
    tex_is_processing: BoolProperty(
        name="Texturing In Progress",
        default=False,
    )

    tex_has_draft: BoolProperty(
        name="Has Draft",
        description="Whether a draft texture has been applied",
        default=False,
    )

    tex_camera_count: IntProperty(
        name="Camera Count",
        default=0,
    )

    tex_status: StringProperty(
        name="Texturing Status",
        default="",
    )


# ─── Main Panel (like Render settings header in Cycles) ───

class BananaPTRenderPanel(Panel):
    """Nano Banana main settings — appears under Render Properties when engine is selected"""
    bl_label = "Nano Banana"
    bl_idname = "BANANA_PT_render_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    COMPAT_ENGINES = {'NANO_BANANA'}
    
    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        scene = context.scene
        props = scene.gemini_render
        
        # Model selector (like Device: CPU/GPU in Cycles)
        layout.prop(props, "ai_model")
        
        # Credit cost hint for current model
        prefs = context.preferences.addons.get("nano_banana_render")
        has_token = prefs and hasattr(prefs.preferences, 'beta_token') and prefs.preferences.beta_token.strip()
        token = prefs.preferences.beta_token.strip() if has_token else ""
        is_credit_user = auth_utils.is_nanode_token(token)
        is_api_user = auth_utils.is_google_api_key(token)
        
        if is_credit_user:
            res = getattr(props, 'resolution', '1024')
            cost = get_image_cost(props.ai_model, res)
            row = layout.row()
            row.scale_y = 0.7
            if cost is None:
                row.alert = True
                row.label(text="Selected model supports 1K only", icon='ERROR')
            else:
                row.label(text=f"Cost: {cost} credits per render")
        
        if not has_token:
            row = layout.row()
            row.alert = True
            row.operator("banana.google_login", text="Login with Google", icon='URL')
        else:
            if not is_api_user:
                # Balance display
                row = layout.row()
                if props.beta_balance >= 0:
                    if is_credit_user:
                        row.label(text=f"Credits: {props.beta_balance}")
                    else:
                        row.label(text=f"Generations left: {props.beta_balance}")
                else:
                    if is_credit_user:
                        row.label(text="Account Active", icon='LINKED')
                    else:
                        row.label(text="Beta Active", icon='LINKED')
                row.operator("banana.refresh_balance", text="", icon='FILE_REFRESH')
                if is_credit_user:
                    row.operator("banana.google_login", text="", icon='URL')
                
                # Buy Credits button for credit users (on the same row)
                if is_credit_user:
                    if props.beta_balance >= 0 and props.beta_balance < 30:
                        row.alert = True
                    row.operator("banana.open_store", text="Buy Credits", icon='PLUS')
                
                # ─── Rating buttons (after render) ────────────────
                if props.last_generation_id > 0 and not props.last_generation_rated:
                    box = layout.box()
                    box.label(text="Rate this result:", icon='QUESTION')
                    row = box.row(align=True)
                    op_like = row.operator(OP_RATE_GEN, text="👍 Good")
                    op_like.rating = "like"
                    op_dislike = row.operator(OP_RATE_GEN, text="👎 Bad")
                    op_dislike.rating = "dislike"
            
            # ─── Feedback section ─────────────────────────────
            if is_api_user:
                bonus_label = ""
            elif is_credit_user:
                bonus_label = "+50 Credits"
            else:
                bonus_label = "+50 Gens"
            
            if props.show_feedback:
                box = layout.box()
                if props.has_submitted_feedback:
                    box.label(text="Leave additional feedback:", icon='INFO')
                else:
                    if bonus_label:
                        box.label(text=f"Leave feedback (min. 50 chars) for {bonus_label}!", icon='INFO')
                    else:
                        box.label(text="Leave feedback (min. 50 chars):", icon='INFO')
                box.prop(props, "feedback_text", text="")
                row = box.row()
                row.enabled = len(props.feedback_text.strip()) >= 50
                row.operator("banana.send_feedback", text="Submit Feedback", icon='CHECKMARK')
            else:
                row = layout.row()
                if props.has_submitted_feedback:
                    row.operator(OP_TOGGLE_FEEDBACK, text="Thanks for your Feedback!", icon='HEART')
                else:
                    text = "Leave Feedback (" + bonus_label + ")" if bonus_label else "Leave Feedback"
                    row.operator(OP_TOGGLE_FEEDBACK, text=text, icon='GREASEPENCIL')
        
        # Status (only show during/after render)
        if props.status_text and props.status_text != "Ready":
            layout.separator()
            box = layout.box()
            status_icon = 'TIME' if props.is_rendering else 'INFO'
            box.label(text=props.status_text, icon=status_icon)


# ─── Prompt Sub-panel ───

class BananaPTPrompt(Panel):
    """Prompt configuration"""
    bl_label = "Prompt"
    bl_idname = "BANANA_PT_prompt"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_parent_id = "BANANA_PT_render_panel"
    COMPAT_ENGINES = {'NANO_BANANA'}
    
    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.gemini_render
        
        layout.prop(props, "prompt", text="")


# ─── Render Mode Sub-panel (like Sampling in Cycles) ───

class BananaPTRenderMode(Panel):
    """Render mode and resolution settings"""
    bl_label = "Render Mode"
    bl_idname = "BANANA_PT_render_mode"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_parent_id = "BANANA_PT_render_panel"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'NANO_BANANA'}
    
    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        props = context.scene.gemini_render
        
        layout.prop(props, "render_mode", text="Mode")
        layout.prop(props, "resolution")
        
        # Warn if 2K/4K selected with a 1K-only image model.
        if not supports_image_resolution(props.ai_model, props.resolution):
            row = layout.row()
            row.alert = True
            row.label(text="Selected model supports 1K only", icon='ERROR')
        
        # Show auto-detected dimensions
        _, _ = get_render_dimensions_from_scene(context)
        


# ─── Mist Settings Sub-panel ───

class BananaPTOmniEngine(Panel):
    """Omni video render engine settings."""
    bl_label = "Omni Engine"
    bl_idname = "BANANA_PT_omni_engine"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    COMPAT_ENGINES = {'NANODE_OMNI'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        props = context.scene.gemini_render
        prefs = context.preferences.addons.get("nano_banana_render")
        token = ""
        if prefs and hasattr(prefs.preferences, 'beta_token'):
            token = prefs.preferences.beta_token.strip()

        is_nanode = auth_utils.is_nanode_token(token)
        is_personal = auth_utils.is_google_api_key(token)
        task = 'edit' if props.omni_input_mode == 'VIDEO_EDIT' else 'image_to_video'
        duration = props.omni_duration or '10'
        cost = get_omni_cost(task, duration)

        model = layout.row()
        model.label(text="Model")
        model.label(text="Gemini Omni Flash")
        row = layout.row()
        row.scale_y = 0.8
        if is_personal:
            row.label(text="Personal Google API / 720p", icon='PREFERENCES')
        else:
            row.label(text=f"Cost: {cost} credits per video")

        if not is_nanode and not is_personal:
            row = layout.row()
            row.alert = True
            row.operator("banana.google_login", text="Login with Google", icon='URL')
        elif is_nanode:
            row = layout.row(align=True)
            if props.beta_balance >= 0:
                row.label(text=f"Credits: {props.beta_balance}")
            else:
                row.label(text="Nanode Account", icon='LINKED')
            row.operator("banana.refresh_balance", text="", icon='FILE_REFRESH')
            row.operator("banana.google_login", text="", icon='URL')
            row.operator("banana.open_store", text="Buy Credits", icon='PLUS')
        else:
            layout.label(text="Advanced local mode", icon='LINKED')

        action = layout.row()
        action.scale_y = 1.25
        action.enabled = (is_nanode or is_personal) and bool(props.prompt.strip())
        action.operator("banana.ai_render", text="Generate One Omni Video", icon='RENDER_ANIMATION')

        warning = layout.row()
        warning.alert = True
        warning.label(text="Do not use Blender Render Animation", icon='ERROR')

        if props.omni_status:
            layout.separator()
            status = layout.box()
            status_value = props.omni_status.lower()
            status_icon = 'ERROR' if "failed" in status_value else 'CHECKMARK' if "ready" in status_value else 'TIME'
            status.label(text=props.omni_status, icon=status_icon)


class BananaPTOmniPrompt(Panel):
    bl_label = "Prompt"
    bl_idname = "BANANA_PT_omni_prompt"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_parent_id = "BANANA_PT_omni_engine"
    COMPAT_ENGINES = {'NANODE_OMNI'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES

    def draw(self, context):
        self.layout.prop(context.scene.gemini_render, "prompt", text="")


class BananaPTOmniSettings(Panel):
    bl_label = "Render Settings"
    bl_idname = "BANANA_PT_omni_settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_parent_id = "BANANA_PT_omni_engine"
    COMPAT_ENGINES = {'NANODE_OMNI'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        props = context.scene.gemini_render
        layout.prop(props, "omni_render_mode")
        layout.prop(props, "omni_input_mode")
        layout.prop(props, "omni_aspect_ratio")
        layout.prop(props, "omni_duration")

        if props.omni_source_video_override:
            source = layout.box()
            row = source.row(align=True)
            row.label(
                text=f"Reusing: {os.path.basename(bpy.path.abspath(props.omni_source_video_override))}",
                icon='FILE_MOVIE',
            )
            row.operator("nanode.omni_clear_reuse_source", text="", icon='X')

        notice = layout.row()
        notice.alert = True
        notice.label(text="Camera supports 16:9 and 9:16 only", icon='INFO')
        if props.omni_input_mode == 'VIDEO_EDIT':
            layout.label(text="Uploads the viewport motion guide", icon='FILE_MOVIE')
        elif props.omni_input_mode == 'TIMELINE_FRAMES':
            layout.label(text="Uses first, middle, and last timeline frames", icon='KEYFRAME_HLT')


class BananaPTOmniStyleReference(Panel):
    bl_label = "Style Reference"
    bl_idname = "BANANA_PT_omni_style_reference"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_parent_id = "BANANA_PT_omni_engine"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'NANODE_OMNI'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        self.layout.prop(context.scene.gemini_render, "use_style_reference", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        props = context.scene.gemini_render
        layout.active = props.use_style_reference
        layout.prop(props, "style_reference_image", text="Image")
        layout.operator("gemini.load_image_as_reference", text="Load from File", icon='FILEBROWSER')
        if props.style_reference_image:
            width, height = props.style_reference_image.size
            layout.label(text=f"{width} x {height}", icon='IMAGE_DATA')


class BananaPTOmniHistory(Panel):
    bl_label = "Video History"
    bl_idname = "BANANA_PT_omni_history"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_parent_id = "BANANA_PT_omni_engine"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'NANODE_OMNI'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES

    def draw(self, context):
        from . import video_director

        video_director.draw_video_history(
            self.layout,
            context,
            omni_only=True,
            show_header=False,
            allow_omni_reuse=True,
        )


class BananaPTMist(Panel):
    """Mist pass settings for depth rendering"""
    bl_label = "Mist Pass"
    bl_idname = "BANANA_PT_mist"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_parent_id = "BANANA_PT_render_panel"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'NANO_BANANA'}
    
    @classmethod
    def poll(cls, context):
        return (context.engine in cls.COMPAT_ENGINES and 
                hasattr(context.scene, 'gemini_render') and 
                context.scene.gemini_render.render_mode == 'DEPTH')
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        props = context.scene.gemini_render
        
        layout.prop(props, "mist_start")
        layout.prop(props, "mist_depth")
        layout.prop(props, "mist_falloff")
        
        layout.separator()
        layout.prop(props, "mist_preview", toggle=True)


# ─── Style Reference Sub-panel ───

class BananaPTStyleReference(Panel):
    """Style reference for AI rendering"""
    bl_label = "Style Reference"
    bl_idname = "BANANA_PT_style_reference"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_parent_id = "BANANA_PT_render_panel"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'NANO_BANANA'}
    
    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES
    
    def draw_header(self, context):
        props = context.scene.gemini_render
        self.layout.prop(props, "use_style_reference", text="")
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        props = context.scene.gemini_render
        layout.active = props.use_style_reference
        
        layout.prop(props, "style_reference_image", text="Image")
        
        # Load from file
        row = layout.row()
        row.operator("gemini.load_image_as_reference", text="Load from File", icon='FILEBROWSER')
        
        if props.style_reference_image:
            col = layout.column(align=True)
            col.scale_y = 0.8
            col.label(text=f"{props.style_reference_image.size[0]}×{props.style_reference_image.size[1]}", icon='IMAGE_DATA')


# ─── Render Gallery Sub-panel ───

class BananaPTHistoryPanel(Panel):
    """Visual gallery render history panel"""
    bl_label = "Render Gallery" 
    bl_idname = "BANANA_PT_history_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_parent_id = "BANANA_PT_render_panel"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'NANO_BANANA'}
    
    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.gemini_render
        
        if len(props.render_history) == 0:
            layout.label(text="No renders yet", icon='INFO')
            from . import video_director

            video_director.draw_video_history(layout, context)
            return
        
        layout.label(text=f"{len(props.render_history)} renders", icon='IMAGE_DATA')
        
        # Gallery — newest first, giant thumbnails
        from . import history_previews
        for i, item in enumerate(reversed(props.render_history)):
            actual_index = len(props.render_history) - 1 - i
            render_number = len(props.render_history) - i
            
            box = layout.box()
            
            # Header
            header = box.row()
            header.label(text=f"#{render_number} \u2022 {item.timestamp}", icon='TIME')
            
            # Giant thumbnail using template_icon (maintains aspect ratio, fills width)
            icon_id = history_previews.get_preview_icon_id_safe(item.filepath, item.image_name)
            if icon_id:
                row = box.row()
                row.template_icon(icon_value=icon_id, scale=8.0)
            else:
                col = box.column(align=True)
                col.scale_y = 3.0
                col.label(text="Loading Preview...", icon='IMAGE_DATA')
            
            # Prompt preview
            prompt_preview = item.prompt[:60] + "..." if len(item.prompt) > 60 else item.prompt
            box.label(text=prompt_preview, icon='TEXT')
            
            # Actions row
            actions = box.row(align=True)
            view_btn = actions.operator("gemini.load_history", text="Open in Editor", icon='ZOOM_IN')
            view_btn.history_index = actual_index

            first_btn = actions.operator("nanode.video_use_render_history", text="First", icon='TRIA_RIGHT')
            first_btn.history_index = actual_index
            first_btn.target = 'FIRST'

            last_btn = actions.operator("nanode.video_use_render_history", text="Last", icon='TRACKING_FORWARDS')
            last_btn.history_index = actual_index
            last_btn.target = 'LAST'
            
            gear_btn = actions.operator("gemini.history_context_menu", text="", icon='DOWNARROW_HLT')
            gear_btn.history_index = actual_index

        layout.separator()
        from . import video_director

        video_director.draw_video_history(layout, context)



# ─── Helper functions ───

def update_mist_settings(self, context):
    """Update world mist settings when main mist UI values change."""
    try:
        if not context.scene.world:
            return
        world = context.scene.world
        mist_start_m = self.mist_start
        mist_depth_m = self.mist_depth
        mist_falloff = self.mist_falloff if hasattr(self, 'mist_falloff') else 'LINEAR'
        if hasattr(world, 'mist_settings'):
            world.mist_settings.use_mist = True
            world.mist_settings.start = mist_start_m
            world.mist_settings.depth = mist_depth_m
            world.mist_settings.falloff = mist_falloff
    except Exception as e:
        print(f"[GEMINI] Failed to update mist settings: {e}")


def update_tex_mist_settings(self, context):
    """Update world mist settings from TEXTURE pipeline depth sliders."""
    try:
        world = context.scene.world
        if not world:
            return
        start = self.tex_depth_start
        depth = self.tex_depth_depth
        falloff = self.mist_falloff if hasattr(self, 'mist_falloff') else 'LINEAR'
        if hasattr(world, 'mist_settings'):
            world.mist_settings.use_mist = True
            world.mist_settings.start = start
            world.mist_settings.depth = depth
            world.mist_settings.falloff = falloff
        # Refresh viewport if mist preview is on
        if self.mist_preview:
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
    except Exception as e:
        print(f"[TEX] Failed to update tex mist settings: {e}")


def on_cam_settings_change(self, context):
    """Auto-update existing cameras when distance/ortho_scale sliders change."""
    try:
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            return
        from . import texture_pipeline as pipe
        # Only update if cameras already exist
        if not any(o.name.startswith(pipe.TEMP_PREFIX + "cam_")
                   for o in bpy.data.objects):
            return
        pipe.update_cameras(
            distance=self.tex_cam_distance,
            ortho_scale=self.tex_cam_ortho_scale,
            target_obj=obj,
        )
    except Exception as e:
        print(f"[TEX] Camera settings update failed: {e}")

def toggle_mist_preview(self, context):
    """Toggle mist preview in 3D viewport."""
    try:
        update_mist_settings(self, context)
        
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        if self.mist_preview:
                            space.shading.type = 'MATERIAL'
                            if hasattr(space.shading, 'render_pass'):
                                space.shading.render_pass = 'MIST'
                        else:
                            if hasattr(space.shading, 'render_pass'):
                                space.shading.render_pass = 'COMBINED'
                            space.shading.type = 'MATERIAL'
                        area.tag_redraw()
                        return
        
    except Exception as e:
        print(f"[GEMINI] Failed to toggle mist preview: {e}")

def on_tex_render_mode_change(self, context):
    """Handle texture render mode change — switch off mist preview if not mist."""
    try:
        if self.tex_render_mode == 'COLOR' and getattr(self, 'mist_preview', False):
            self.mist_preview = False
    except AttributeError:
        pass

def on_render_mode_change(self, context):
    """Handle render mode change — switch viewport to match mode."""
    try:
        # Disable mist preview if switching to EEVEE
        if self.render_mode == 'EEVEE' and self.mist_preview:
            self.mist_preview = False
        
        # Auto-switch viewport shading to match render mode
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        if self.render_mode == 'DEPTH':
                            # Switch to Material mode with Mist pass
                            space.shading.type = 'MATERIAL'
                            if hasattr(space.shading, 'render_pass'):
                                space.shading.render_pass = 'MIST'
                            if hasattr(space.shading, 'use_scene_world'):
                                space.shading.use_scene_world = True
                            # Update mist settings so the preview is accurate
                            update_mist_settings(self, context)
                        else:
                            # Switch to Material Preview (EEVEE-like)
                            space.shading.type = 'MATERIAL'
                            if hasattr(space.shading, 'render_pass'):
                                space.shading.render_pass = 'COMBINED'
                            if hasattr(space.shading, 'use_scene_lights'):
                                space.shading.use_scene_lights = True
                        area.tag_redraw()
                        return
    except Exception as e:
        print(f"[NANO BANANA] Render mode change error: {e}")


def get_render_dimensions_from_scene(context) -> tuple:
    """Get render dimensions from scene settings with base resolution scaling."""
    try:
        scene = context.scene
        props = scene.gemini_render if hasattr(scene, 'gemini_render') else None
        base = int(props.resolution) if props else 1024
        
        render = scene.render
        scene_width = render.resolution_x
        scene_height = render.resolution_y
        
        aspect = scene_width / scene_height
        
        if aspect >= 1.0:
            width = base
            height = int(base / aspect)
        else:
            height = base
            width = int(base * aspect)
        
        return (width, height)
    except Exception:
        return (1024, 1024)


def get_scene_aspect_ratio_string(context) -> str:
    """Get the closest supported aspect ratio string for Gemini API."""
    try:
        scene = context.scene
        render = scene.render
        aspect = render.resolution_x / render.resolution_y
        
        ratios = {
            "1:1": 1.0,
            "16:9": 16/9,
            "9:16": 9/16,
            "4:3": 4/3,
            "3:2": 3/2
        }
        closest = min(ratios.items(), key=lambda x: abs(x[1] - aspect))
        return closest[0]
    except Exception:
        return "1:1"


# ─── AI Texturing N-Panel (3D Viewport) ───────────────────────────

class BananaPTTexturingNpanel(Panel):
    """AI Texturing panel — appears in the 3D Viewport sidebar (N-key)"""
    bl_label = "Nanode AI Texturing (Beta)"
    bl_idname = "BANANA_PT_texturing_npanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Nanode AI Texturing (Beta)"
    bl_options = set()

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.mode == 'OBJECT')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.gemini_render
        obj = context.active_object

        # ── Auth ──
        prefs = context.preferences.addons.get("nano_banana_render")
        has_token = (prefs and hasattr(prefs.preferences, 'beta_token')
                     and prefs.preferences.beta_token.strip())
        token = prefs.preferences.beta_token.strip() if has_token else ""
        is_direct_api = auth_utils.is_google_api_key(token)
        is_credit_user = auth_utils.is_nanode_token(token)

        if not has_token:
            box = layout.box()
            box.alert = True
            box.label(text="No API key!", icon='ERROR')
            box.operator("banana.google_login", text="Login with Google", icon='URL')
            return

        # ── Object info ──
        row = layout.row()
        row.label(text=f"Object: {obj.name}", icon='OBJECT_DATA')

        layout.separator()

        # ── Generation Settings (Model & Resolution) ──
        gen_box = layout.box()
        gen_box.prop(props, "ai_model")
        gen_box.prop(props, "tex_resolution")
        # Warning about projection vs texture resolution
        warn_row = gen_box.row()
        warn_row.scale_y = 0.65
        warn_row.label(text="Per-view projection size, not final texture resolution", icon='INFO')

        layout.separator()

        # ── Prompt ──
        layout.label(text="Texture Description:", icon='TEXT')
        layout.prop(props, "tex_prompt", text="")

        # ── Style Reference Image ──
        ref_box = layout.box()
        ref_box.label(text="Style Reference:", icon='IMAGE_DATA')
        row = ref_box.row(align=True)
        row.prop(props, "tex_reference_image", text="")
        row.operator("banana.load_tex_reference", text="", icon='FILEBROWSER')
        if props.tex_reference_image:
            row.operator("banana.clear_tex_reference", text="", icon='X')
            ref_box.label(text=f"✓ {props.tex_reference_image.name}", icon='CHECKMARK')

        # ── Balance & Credits ──
        if is_credit_user:
            box = layout.box()
            row = box.row(align=True)
            if props.beta_balance >= 0:
                row.label(text=f"Credits: {props.beta_balance}")
            else:
                row.label(text="Credits: ...")
            row.operator("banana.refresh_balance", text="", icon='FILE_REFRESH')
            op = row.operator("wm.url_open", text="Buy Credits", icon='PLUS')
            op.url = "https://nanode.tech/pricing/"

        # ── Rating ──
        if props.last_generation_id > 0 and not props.last_generation_rated:
            rate_box = layout.box()
            rate_box.label(text="Rate this result:", icon='QUESTION')
            rate_box.row(align=True).operator(OP_RATE_GEN, text="👍 Good").rating = "like"
            rate_box.row(align=True).operator(OP_RATE_GEN, text="👎 Bad").rating = "dislike"

        # ── Feedback ──
        if hasattr(props, 'show_feedback'):
            if props.show_feedback:
                fb_box = layout.box()
                if props.has_submitted_feedback:
                    fb_box.label(text="Leave additional feedback:", icon='INFO')
                else:
                    fb_box.label(text="Feedback (50+ chars) for +50 generations!", icon='INFO')
                fb_box.prop(props, "feedback_text", text="")
                row = fb_box.row()
                row.enabled = len(props.feedback_text.strip()) >= 50
                row.operator("banana.send_feedback", text="Submit Feedback", icon='CHECKMARK')
            else:
                row = layout.row()
                if props.has_submitted_feedback:
                    row.operator(OP_TOGGLE_FEEDBACK, text="Thanks for your Feedback!", icon='CHECKMARK')
                else:
                    row.operator(OP_TOGGLE_FEEDBACK, text="Leave Feedback (+50 Credits)", icon='OUTLINER_OB_LIGHT')

        layout.separator()

        # ═══════════════ Camera Setup ═══════════════
        cam_box = layout.box()
        cam_head = cam_box.row()
        icon = 'TRIA_DOWN' if props.tex_ui_show_cam_setup else 'TRIA_RIGHT'
        cam_head.prop(props, "tex_ui_show_cam_setup", icon=icon, text="Camera Setup", emboss=False)

        if props.tex_ui_show_cam_setup:
            cam_box.separator()
            cam_box.prop(props, "tex_camera_preset", text="Layout")
    
            row = cam_box.row(align=True)
            row.prop(props, "tex_include_top", text="Top", toggle=True)
            row.prop(props, "tex_include_bottom", text="Bottom", toggle=True)
    
            # Camera distance + ortho scale
            col = cam_box.column(align=True)
            col.prop(props, "tex_cam_distance", text="Distance")
            col.prop(props, "tex_cam_ortho_scale", text="Ortho Scale")
    
            # Init / Update camera buttons
            from . import texture_pipeline as _pipe
            num_cams = len(_pipe.generate_camera_views(
                props.tex_camera_preset,
                props.tex_include_top,
                props.tex_include_bottom,
            ))
            has_cams = any(
                o.name.startswith("nb_tex_cam_") for o in bpy.data.objects
            )
    
            row = cam_box.row(align=True)
            row.scale_y = 1.3
            btn_text = (f"Re-Init ({num_cams})"
                        if has_cams else f"Init Cameras ({num_cams})")
            row.operator("banana.init_tex_cameras", text=btn_text,
                         icon='OUTLINER_OB_CAMERA')
            if has_cams:
                row.operator("banana.update_tex_cameras", text="",
                             icon='FILE_REFRESH')
    
            # ── Camera preview buttons (scan existing cameras) ──
            if has_cams:
                cam_box.separator()
                cam_box.label(text="Preview:", icon='RESTRICT_VIEW_OFF')
    
                prefix = "nb_tex_cam_"
                view_names = sorted(
                    o.name[len(prefix):]
                    for o in bpy.data.objects
                    if o.name.startswith(prefix)
                )
    
                # 3 buttons per row
                for i in range(0, len(view_names), 3):
                    row = cam_box.row(align=True)
                    for name in view_names[i:i+3]:
                        op = row.operator("banana.preview_tex_camera",
                                         text=name)
                        op.camera_name = name

        layout.separator()

        # ═══════════════ Render Mode ═══════════════
        layout.prop(props, "tex_render_mode", text="Render Type")

        layout.separator()

        # ═══════════════ Depth / Mist Settings ═══════════════
        if props.tex_render_mode == 'MIST':
            depth_box = layout.box()
            depth_head = depth_box.row()
            icon = 'TRIA_DOWN' if props.tex_ui_show_depth_setup else 'TRIA_RIGHT'
            depth_head.prop(props, "tex_ui_show_depth_setup", icon=icon, text="Depth Settings (Mist Pass)", emboss=False)
            
            if props.tex_ui_show_depth_setup:
                depth_box.separator()
                col = depth_box.column(align=True)
                col.prop(props, "tex_depth_start", text="Start")
                col.prop(props, "tex_depth_depth", text="Depth")
                col.prop(props, "mist_falloff", text="Falloff")
    
                # Preview mist toggle
                row = depth_box.row()
                row.prop(props, "mist_preview", toggle=True, icon='HIDE_OFF')

            layout.separator()

        # ═══════════════ Generation ═══════════════
        has_cams = any(o.name.startswith("nb_tex_cam_") for o in bpy.data.objects)
        if has_cams:
            # Draft button
            col = layout.column()
            col.scale_y = 1.4
            col.enabled = not props.tex_is_processing
            col.operator("banana.texture_draft",
                         text="Generate Texture", icon='BRUSH_DATA')

            # Cost hint
            if not is_direct_api:
                draft_cost = _get_cost_per_request_ui(props)
                sub = layout.row()
                sub.scale_y = 0.7
                if draft_cost <= 0:
                    sub.alert = True
                    sub.label(text="Selected model supports 1K only", icon='ERROR')
                else:
                    sub.label(text=f"{draft_cost} credits (1 request)")
        else:
            layout.label(text="Init cameras to start generation", icon='INFO')

        layout.separator()

        # Cleanup
        if has_cams:
            row = layout.row()
            row.operator("banana.cleanup_tex", text="Cleanup", icon='TRASH')

        # ── Status bar ──
        if props.tex_status:
            layout.separator()
            box = layout.box()
            icon = 'TIME' if props.tex_is_processing else 'INFO'
            box.label(text=props.tex_status, icon=icon)


def _get_cost_per_request_ui(props) -> int:
    """Calculate cost per request for UI display."""
    res = getattr(props, 'tex_resolution', '1024')
    return get_image_cost(props.ai_model, res) or 0
