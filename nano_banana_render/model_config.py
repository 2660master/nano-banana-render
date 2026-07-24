IMAGE_MODEL_ITEMS = [
    ("NANO_BANANA_2_LITE", "Nano Banana 2 Lite", "gemini-3.1-flash-lite-image - fastest, 1K only"),
    ("NANO_BANANA_2", "Nano Banana 2", "gemini-3.1-flash-image - fast, balanced quality"),
    ("NANO_BANANA_PRO", "Nano Banana Pro", "gemini-3-pro-image - highest quality"),
    ("NANO_BANANA", "Nano Banana", "gemini-2.5-flash-image - legacy 1K"),
]

MODEL_MAP = {
    "NANO_BANANA_2_LITE": "gemini-3.1-flash-lite-image",
    "NANO_BANANA_2": "gemini-3.1-flash-image",
    "NANO_BANANA_PRO": "gemini-3-pro-image",
    "NANO_BANANA": "gemini-2.5-flash-image",
}

IMAGE_COSTS = {
    "NANO_BANANA_2_LITE": {"1024": 5, "2048": None, "4096": None, "AUTO": 5},
    "NANO_BANANA_2": {"1024": 10, "2048": 15, "4096": 60, "AUTO": 10},
    "NANO_BANANA_PRO": {"1024": 30, "2048": 45, "4096": 60, "AUTO": 30},
    "NANO_BANANA": {"1024": 10, "2048": None, "4096": None, "AUTO": 10},
}

OMNI_TASK_ITEMS = [
    ("auto", "Auto Director", "Choose the best Omni video task from the current context"),
    ("image_to_video", "Animate Current Frame", "Animate the current render or viewport frame"),
    ("reference_to_video", "Reference Motion", "Use references to guide motion and style"),
    ("edit", "Edit Last Clip", "Iteratively edit the latest Omni clip"),
]

VIDEO_DURATION_ITEMS = [
    ("4", "4s", "Short motion test"),
    ("6", "6s", "Balanced video length"),
    ("8", "8s", "Longest supported clip"),
]

OMNI_DURATION_ITEMS = [
    ("4", "4s", "Short motion test"),
    ("6", "6s", "Balanced video length"),
    ("8", "8s", "Longer video"),
    ("10", "10s", "Maximum Gemini Omni Flash output length"),
]

VIDEO_EDIT_DURATION_ITEMS = [
    ("AUTO", "Auto", "Match the source video duration"),
    *OMNI_DURATION_ITEMS,
]

VEO_MODEL_ITEMS = [
    ("veo-3.1-lite-generate-preview", "Veo 3.1 Lite", "Cost-efficient video generation"),
    ("veo-3.1-fast-generate-preview", "Veo 3.1 Fast", "Fast video generation"),
    ("veo-3.1-generate-preview", "Veo 3.1 Standard", "Highest quality Veo generation"),
]

VIDEO_MODEL_ITEMS = [
    ("gemini-omni-flash-preview", "Gemini Omni Flash", "Flexible 720p video generation and editing"),
    *VEO_MODEL_ITEMS,
]

VIDEO_DIRECTOR_TASK_ITEMS = [
    ("auto", "Auto Director", "Let Omni choose the best generation workflow", 0),
    ("text_to_video", "Text to Video", "Generate a shot from a text prompt", 1),
    ("image_to_video", "Image to Video", "Animate a selected first frame", 2),
    ("first_last", "First / Last Frames", "Generate motion between two selected frames", 3),
    ("reference_to_video", "Reference Images", "Guide the subject with reference images", 4),
    ("edit", "Edit Video", "Transform an existing video while preserving its motion", 5),
]

VIDEO_RESOLUTION_ITEMS = [
    ("720p", "720p", "Fastest and cheapest", 0),
    ("1080p", "1080p", "Requires 8 seconds", 1),
    ("4k", "4K", "Requires 8 seconds, unavailable on Lite", 2),
]

VIDEO_ASPECT_ITEMS = [
    ("16:9", "16:9", "Landscape"),
    ("9:16", "9:16", "Vertical"),
]

OMNI_CREDITS_PER_SECOND = {
    "auto": 20,
    "text_to_video": 20,
    "image_to_video": 20,
    "reference_to_video": 22,
    "edit": 24,
}

VEO_CREDITS_PER_SECOND = {
    "veo-3.1-lite-generate-preview": {"720p": 10, "1080p": 15},
    "veo-3.1-fast-generate-preview": {"720p": 20, "1080p": 24, "4k": 60},
    "veo-3.1-generate-preview": {"720p": 75, "1080p": 75, "4k": 115},
}


def get_model_name(model_key: str) -> str:
    return MODEL_MAP.get(model_key, MODEL_MAP["NANO_BANANA_2"])


def get_image_cost(model_key: str, resolution: str) -> int | None:
    return IMAGE_COSTS.get(model_key, IMAGE_COSTS["NANO_BANANA_PRO"]).get(str(resolution), 30)


def supports_image_resolution(model_key: str, resolution: str) -> bool:
    return get_image_cost(model_key, resolution) is not None


def get_omni_cost(task: str, duration: str | int) -> int:
    duration_int = int(duration)
    return OMNI_CREDITS_PER_SECOND.get(task, OMNI_CREDITS_PER_SECOND["auto"]) * duration_int


def get_veo_cost(model: str, resolution: str, duration: str | int) -> int | None:
    per_second = VEO_CREDITS_PER_SECOND.get(model, {}).get(resolution)
    if per_second is None:
        return None
    return per_second * int(duration)


def is_omni_model(model: str) -> bool:
    return model == "gemini-omni-flash-preview"


def get_video_cost(model: str, task: str, resolution: str, duration: str | int) -> int | None:
    if is_omni_model(model):
        if resolution != "720p":
            return None
        omni_task = task if task in OMNI_CREDITS_PER_SECOND else "auto"
        return get_omni_cost(omni_task, duration)
    return get_veo_cost(model, resolution, duration)
