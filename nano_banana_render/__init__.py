bl_info = {
    "name": "Nanode AI Render Engine",
    "blender": (4, 5, 0),  # Minimum version, supports up to 5.0+
    "category": "Render", 
    "version": (2, 8, 0),
    "author": "Kovname",
    "description": "Generative Pipeline for Blender",
    "location": "Render Properties, Image Editor, and Nanode N-panel",
    "doc_url": "https://nanode.tech/",
    "tracker_url": "https://github.com/Kovname/nano-banana-render/issues",
}

# Build number — increment this for hotfix releases without changing bl_info["version"].
# The updater checks both version AND build number, so users get prompted even for same-version fixes.
BUILD_NUMBER = 15
# Blender version compatibility helpers
def get_blender_version():
    """Get Blender version as tuple (major, minor, patch)"""
    import bpy
    return bpy.app.version

def is_blender_5():
    """Check if running on Blender 5.0+"""
    import bpy
    return bpy.app.version >= (5, 0, 0)

import bpy
from bpy.app.handlers import persistent
from bpy.types import AddonPreferences
from bpy.props import StringProperty, BoolProperty

# Reload modules for development
if "bpy" in locals():
    import importlib
    if "log" in locals():
        importlib.reload(log)
    if "credentials" in locals():
        importlib.reload(credentials)
    if "auth_utils" in locals():
        importlib.reload(auth_utils)
    if "model_config" in locals():
        importlib.reload(model_config)
    if "ui_panel" in locals():
        importlib.reload(ui_panel)
    if "operators" in locals():
        importlib.reload(operators)
    if "depth_utils" in locals():
        importlib.reload(depth_utils)
    if "gemini_api" in locals():
        importlib.reload(gemini_api)
    if "threading_utils" in locals():
        importlib.reload(threading_utils)
    if "image_editor" in locals():
        importlib.reload(image_editor)
    if "video_director" in locals():
        importlib.reload(video_director)
    if "smart_points" in locals():
        importlib.reload(smart_points)
    if "image_edit_thread" in locals():
        importlib.reload(image_edit_thread)
    if "render_engine" in locals():
        importlib.reload(render_engine)
    if "beta_api" in locals():
        importlib.reload(beta_api)
    if "texture_pipeline" in locals():
        importlib.reload(texture_pipeline)
    if "texture_operators" in locals():
        importlib.reload(texture_operators)
    if "updater" in locals():
        importlib.reload(updater)
    if "history_previews" in locals():
        try:
            history_previews.clear_previews()
        except Exception:
            pass
        importlib.reload(history_previews)

# Import our modules
from . import log
from . import credentials
from . import auth_utils
from . import model_config
from . import ui_panel
from . import operators
from . import depth_utils
from . import gemini_api
from . import threading_utils
from . import image_editor
from . import video_director
from . import smart_points
from . import image_edit_thread
from . import render_engine
from . import beta_api
from . import texture_pipeline
from . import texture_operators
from . import updater
from . import history_previews

def get_hwid_stable() -> str:
    """Generate a stable 16-char Hardware ID hash based on MAC address."""
    import uuid
    import hashlib
    mac = str(uuid.getnode()).encode('utf-8')
    return hashlib.sha256(mac).hexdigest()[:16]

class NanoBananaPreferences(AddonPreferences):
    bl_idname = __name__

    beta_token: StringProperty(
        name="API Key",
        description="Nanode login token or personal Google AI Studio API key",
        default="",
        subtype='PASSWORD',
    )
    
    eu_format: BoolProperty(
        name="Allow sending generation data to improve Nanode",
        description="When enabled, your generation parameters are sent to our server for additional processing. Your personal API keys remain only on your device and are never transmitted.",
        default=True,
    )

    hwid: StringProperty(
        name="Hardware ID",
        default="",
        options={'HIDDEN'},
    )

    # Account info display — show email on logged-in state
    def draw(self, context):
        layout = self.layout
        token = self.beta_token.strip()
        is_nanode = auth_utils.is_nanode_token(token)
        is_personal_google = auth_utils.is_google_api_key(token)
        email = credentials.get_user_email()
        name = credentials.get_user_name()

        account_box = layout.box()
        account_box.label(text="Nanode Login", icon='USER')
        if is_nanode:
            if email:
                account_box.label(text=email, icon='LINKED')
                if name:
                    row = account_box.row()
                    row.scale_y = 0.7
                    row.label(text=f"     {name}")
            else:
                account_box.label(text="Nanode Account", icon='LINKED')

            row = account_box.row(align=True)
            row.operator("banana.refresh_balance", text="Refresh Balance", icon='FILE_REFRESH')
            row.operator("banana.google_login", text="Reconnect Google", icon='URL')
            row.operator("banana.logout", text="Log Out", icon='PANEL_CLOSE')
            row = account_box.row()
            row.scale_y = 1.2
            row.operator("banana.open_store", text="Buy More Credits", icon='PLUS')
        else:
            col = account_box.column(align=True)
            col.scale_y = 1.4
            col.operator("banana.google_login", text="Login with Google", icon='URL')

        advanced_box = layout.box()
        advanced_box.label(text="Personal API Key", icon='PREFERENCES')
        if is_personal_google:
            advanced_box.label(text="Advanced local mode active", icon='LINKED')
            row = advanced_box.row(align=True)
            row.prop(self, "beta_token", text="Google API Key")
            row.operator("banana.logout", text="", icon='X')
        elif is_nanode:
            advanced_box.label(text="Nanode credits are active. Your Nanode key is hidden.", icon='INFO')
        else:
            advanced_box.label(text="Optional: use your own Google key without Nanode credits.", icon='INFO')
            advanced_box.prop(self, "beta_token", text="Google API Key")

        privacy_box = layout.box()
        privacy_box.label(text="Privacy & Data Collection:", icon='LOCKED')
        privacy_box.prop(self, "eu_format")


# Registration - Core classes first
core_classes = (
    NanoBananaPreferences,
    ui_panel.GeminiRenderHistoryItem,
    ui_panel.GeminiRenderProperties,
    ui_panel.BananaPTRenderPanel,
    ui_panel.BananaPTPrompt,
    ui_panel.BananaPTRenderMode,
    ui_panel.BananaPTOmniEngine,
    ui_panel.BananaPTOmniPrompt,
    ui_panel.BananaPTOmniSettings,
    ui_panel.BananaPTOmniStyleReference,
    ui_panel.BananaPTOmniHistory,
    ui_panel.BananaPTMist,
    ui_panel.BananaPTStyleReference,
    ui_panel.BananaPTHistoryPanel,
    operators.GeminiOTAIRender,
    operators.GeminiOTStopRender,
    operators.GeminiOTLoadHistory,
    operators.GeminiOTDeleteHistory,
    operators.GeminiOTUseHistoryPrompt,
    operators.GeminiOTUseHistoryStyle,
    operators.GeminiOTUseHistoryBoth,
    operators.GeminiOTHistoryContextMenu,
    operators.GeminiOTOpenHistoryImage,
    operators.GeminiOTLoadImageAsReference,
    operators.GeminiOTOpenApiKeyUrl,
    operators.GeminiOTValidateApiKey,
    operators.GeminiOTOpenPreferences,
    operators.BananaOTSendFeedback,
    operators.BananaOTRateGeneration,
    operators.BananaOTRefreshBalance,
    operators.BananaOTToggleFeedback,
    operators.BananaOTGoogleLogin,
    operators.BananaOTLogout,
    operators.BananaOTOpenStore,
    operators.BananaOTShowNoCreditsPopup,
    ui_panel.BananaPTTexturingNpanel,
    texture_operators.BananaOTInitTexCameras,
    texture_operators.BananaOTUpdateTexCameras,
    texture_operators.BananaOTPreviewTexCamera,
    texture_operators.BananaOTTextureDraft,
    texture_operators.BananaOTTextureEnhance,
    texture_operators.BananaOTCleanupTex,
    texture_operators.BananaOTClearTexReference,
    texture_operators.BananaOTLoadTexReference,
    updater.NanodeOTInstallUpdate,
    updater.NanodeOTUpdateDialog,
)

# All core classes combined
classes = core_classes


@persistent
def _nanode_load_post(_dummy):
    try:
        render_engine.reset_runtime_state()
        video_director.reset_runtime_state()
    except Exception as e:
        print(f"[NANO BANANA] Could not reset video runtime after file load: {e}")

    try:
        threading_utils.reset_main_thread_timer_state()
    except Exception:
        pass

    try:
        credentials.restore_credentials_on_startup()
    except Exception as e:
        print(f"[NANO BANANA] Could not restore credentials after file load: {e}")

    for scene in bpy.data.scenes:
        if not hasattr(scene, "gemini_render"):
            continue
        props = scene.gemini_render
        props.is_rendering = False
        if props.status_text.startswith("Starting") or props.status_text.startswith("Rendering"):
            props.status_text = "Ready"

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()

    def _resume_video_jobs():
        try:
            video_director.resume_pending_jobs()
        except Exception as e:
            print(f"[NANODE VIDEO] Could not resume pending jobs: {e}")
        return None

    bpy.app.timers.register(_resume_video_jobs, first_interval=0.5)


def register():
    # Register render engine first
    try:
        render_engine.register()
        print("[NANO BANANA] Render engine registered")
    except Exception as e:
        print(f"Error registering render engine: {e}")
    
    # Register core classes
    for cls in core_classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Error registering core class {cls}: {e}")
    
    # Init history previews gallery
    history_previews.init_previews()

    # Add properties before modules that draw/use them
    if not hasattr(bpy.types.Scene, 'gemini_render'):
        bpy.types.Scene.gemini_render = bpy.props.PointerProperty(type=ui_panel.GeminiRenderProperties)

    if not hasattr(bpy.types.WindowManager, 'history_menu_index'):
        bpy.types.WindowManager.history_menu_index = bpy.props.IntProperty(
            name="History Menu Index",
            description="Index for history context menu",
            default=0
        )
    
    # Register Image Editor module
    try:
        image_editor.register()
        print("[NANO BANANA] Image Editor panel registered")
    except Exception as e:
        print(f"Warning: Could not register Image Editor: {e}")

    try:
        video_director.register()
        print("[NANO BANANA] Video Director panel registered")
    except Exception as e:
        print(f"Warning: Could not register Video Director: {e}")

    if _nanode_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_nanode_load_post)
    
    # Restore saved credentials on startup
    try:
        credentials.restore_credentials_on_startup()
    except Exception as e:
        print(f"[NANO BANANA] Could not restore credentials: {e}")

    # Auto-Updater
    bpy.types.WindowManager.nanode_update_version = StringProperty(default="")
    import threading
    t = threading.Thread(target=updater.check_updates_in_background, args=(bl_info["version"], BUILD_NUMBER), daemon=True)
    t.start()
    if not bpy.app.timers.is_registered(updater.update_poll_timer):
        bpy.app.timers.register(updater.update_poll_timer, first_interval=3.0)

def unregister():
    if _nanode_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_nanode_load_post)

    # Clear history previews gallery
    history_previews.clear_previews()

    # Unregister render engine
    try:
        render_engine.unregister()
    except Exception:
        pass
    
    # Stop any background threads
    try:
        threading_utils.stop_thread_manager()
    except Exception:
        pass
        
    if bpy.app.timers.is_registered(updater.update_poll_timer):
        bpy.app.timers.unregister(updater.update_poll_timer)
    
    # Unregister Image Editor module
    try:
        image_editor.unregister()
    except Exception:
        pass

    try:
        video_director.unregister()
    except Exception:
        pass
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Remove properties from scene
    if hasattr(bpy.types.Scene, 'gemini_render'):
        del bpy.types.Scene.gemini_render
    
    # Remove properties from window manager
    if hasattr(bpy.types.WindowManager, 'history_menu_index'):
        del bpy.types.WindowManager.history_menu_index

if __name__ == "__main__":
    register()
