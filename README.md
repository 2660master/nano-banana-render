<div align="center">

# Nanode AI Render Engine

**Native Gemini image and video workflows for Blender**

[Website](https://nanode.tech) |
[Documentation](https://nanode.tech/docs/#installation) |
[Download](https://github.com/Kovname/nano-banana-render/releases) |
[Pricing](https://nanode.tech/pricing) |
[Issues](https://github.com/Kovname/nano-banana-render/issues)

[![Version](https://img.shields.io/badge/version-2.8.0-ffc400?style=flat-square)](https://github.com/Kovname/nano-banana-render/releases)
[![Blender](https://img.shields.io/badge/Blender-4.5%20%7C%205.0-f5792a?style=flat-square&logo=blender&logoColor=white)](https://www.blender.org/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-image%20%2B%20video-4285f4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-GPL--3.0-2ea44f?style=flat-square)](LICENSE)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=Kovname_nano-banana-render&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Kovname_nano-banana-render)

</div>

Nanode turns Blender blockouts, Eevee renders, animation guides, and reference images into finished AI-assisted images and videos. It works as native Blender render engines and editor panels, so generated media stays inside the scene, Render History, Image Editor, and Video Sequencer.

## What's New in 2.8

- **Omni Engine** renders a rough Blender animation into a finished 720p video while preserving camera motion, timing, subject movement, geometry, and composition.
- **Eevee or Workbench source capture** lets you choose between an already-lit Eevee guide and a clean geometry-focused Workbench guide.
- **Style Reference for video** transfers rendering medium, materials, lighting, palette, texture treatment, and color grade without copying objects from the reference.
- **Nanode Video** adds a dedicated Video Sequencer panel for text-to-video, image-to-video, reference images, first/last frames, and video editing.
- **Gemini Omni Flash** supports uploaded-motion editing, automatic source-duration matching, `16:9` and `9:16`, generated audio, and 4/6/8/10 second workflows.
- **Veo 3.1 Lite, Fast, and Standard** are available for explicit video generation at supported 720p, 1080p, and 4K configurations.
- **Continue from Playhead** captures any visible Sequencer frame and uses it as the first frame for a new generation with the currently selected video model.
- **Unified video history** restores results to the current scene, loads video and audio strips, and supports reusing an Omni motion guide without starting a generation.
- **Nano Banana 2 Lite** adds the lowest-cost image model: `gemini-3.1-flash-lite-image`, 1K output, 5 credits.
- **New Google API keys** are supported in Personal API mode, including both `AQ...` and legacy `AIza...` key formats.
- **Safer paid jobs** use unique request IDs, credit reservation, automatic finalization, and refund on API or safety failure.

## Video Examples

Click a preview to open the full video.

<table>
  <tr>
    <th width="33%">1. Eevee Motion Guide</th>
    <th width="33%">2. Omni Render</th>
    <th width="33%">3. Omni + Style Reference</th>
  </tr>
  <tr>
    <td><a href="docs/videos/1.mp4"><img src="docs/videos/omni-eevee-motion-guide.gif" alt="Eevee motion guide animation"></a></td>
    <td><a href="docs/videos/2.mp4"><img src="docs/videos/omni-render.gif" alt="Omni render animation"></a></td>
    <td><a href="docs/videos/3.mp4"><img src="docs/videos/omni-style-reference.gif" alt="Omni style reference animation"></a></td>
  </tr>
  <tr>
    <td>Original camera, animation, timing, and scene layout rendered with Eevee.</td>
    <td>Finished materials, lighting, shading, reflections, atmosphere, and color grade.</td>
    <td>The same motion and subject identity rendered in the visual language of a reference image.</td>
  </tr>
</table>

## Supported Models

### Image generation

| Nanode name | Google model | Output | Nanode credits |
| --- | --- | ---: | ---: |
| Nano Banana 2 Lite | `gemini-3.1-flash-lite-image` | 1K | 5 |
| Nano Banana 2 | `gemini-3.1-flash-image` | 1K / 2K / 4K | 10 / 15 / 60 |
| Nano Banana Pro | `gemini-3-pro-image` | 1K / 2K / 4K | 30 / 45 / 60 |
| Nano Banana | `gemini-2.5-flash-image` | 1K | 10 |

### Video generation

| Model | Best for | Resolution |
| --- | --- | --- |
| Gemini Omni Flash | Animation rendering, video editing, style-guided video | 720p |
| Veo 3.1 Lite | Lowest-cost standalone video generation | 720p / 1080p |
| Veo 3.1 Fast | Faster production video and higher resolutions | 720p / 1080p / 4K |
| Veo 3.1 Standard | Highest-quality Veo generation | 720p / 1080p / 4K |

Higher-resolution Veo jobs use 8-second output where required by the model.

## Blender Workflows

### Nano Banana Render Engine

- Convert depth/mist passes into finished images while retaining camera and scene geometry.
- Enhance Eevee renders with better materials, lighting, texture detail, and atmosphere.
- Generate 1K, 2K, or 4K output depending on the selected model.
- Apply style references without copying their subjects or composition.
- Browse visual Render History and restore exact generated images.

### Omni Engine

- Capture the active animation using Eevee or Workbench.
- Upload the motion guide as a single video with the selected `16:9` or `9:16` camera.
- Re-render motion, camera, timing, and scene structure with AI-generated shading.
- Add an optional style reference for materials, lighting, palette, and final grade.
- Load successful video and audio directly into the current scene's Sequencer.
- Reuse the original motion guide and prompt from Video History.

### Nanode Video

Available in the Video Sequencer sidebar under `Nanode Video`.

- Generate with Gemini Omni Flash or Veo 3.1.
- Start from text, an image, reference images, or supported first/last frames.
- Select frames directly from Render History or capture the current Sequencer playhead.
- Queue jobs, monitor progress, estimate credits, and restore completed results.
- Continue a generated clip from any visible frame with another supported model.

### AI Video Editor

- Select a Movie Strip, generated result, or local video file.
- Edit with a text prompt while preserving duration, motion, camera path, and identity.
- Match source duration automatically or select a compatible duration manually.
- Apply an optional image as a strict visual-style reference.
- Return the edited clip and its audio to the Video Sequencer.

### Nanode AI Editor

- Perform full-frame image edits from a text prompt.
- Paint masks directly in Blender for inpainting.
- Use Smart Points for precise localized instructions.
- Add reference objects with matched lighting and shadows.
- Browse and restore visual edit history.

### Nanode AI Texturing

- Generate context-aware materials directly on Blender objects.
- Use multi-angle projection cameras for more complete coverage.
- Guide material generation with a style-reference image.

## Documentation

<div align="center">

Installation, authentication, render engines, video workflows, model settings, and troubleshooting are maintained in the Nanode documentation.

[![Open Nanode Documentation](https://img.shields.io/badge/Open_Nanode_Documentation-Installation_and_Workflows-ffc400?style=for-the-badge&labelColor=171717)](https://nanode.tech/docs/#installation)

**[Read the documentation](https://nanode.tech/docs/#installation)**

</div>

## Image Examples

### Depth to render

| Depth input | Result |
| :---: | :---: |
| <img src="docs/images/depth_input.png" alt="Depth input" height="300"> | <img src="docs/images/depth_result.png" alt="Generated render" height="300"> |

### Eevee enhancement

| Eevee draft | Result |
| :---: | :---: |
| <img src="docs/images/reg_render.png" alt="Eevee draft" height="300"> | <img src="docs/images/reg_prompt_result.png" alt="Enhanced result" height="300"> |

### Style-guided image rendering

| Eevee draft | Style reference | Result |
| :---: | :---: | :---: |
| <img src="docs/images/reg_render_2.png" alt="Eevee draft" height="260"> | <img src="docs/images/style_ref_2.png" alt="Style reference" height="260"> | <img src="docs/images/reg_prompt_result_2.png" alt="Style-guided result" height="260"> |

### AI texturing

| Plain object | Textured result |
| :---: | :---: |
| <img src="docs/images/texture_input.gif" alt="Plain object" height="300"> | <img src="docs/images/texture_result.gif" alt="AI-textured result" height="300"> |

### Smart Points

| Target points | Instructions | Result |
| :---: | :---: | :---: |
| <img src="docs/images/smart_points_input.png" alt="Smart Points input" height="260"> | <img src="docs/images/smart_points_prompt.png" alt="Smart Points instructions" height="260"> | <img src="docs/images/smart_points_result.png" alt="Smart Points result" height="260"> |

## Credits and Reliability

- New Nanode accounts receive starter credits after Google login.
- Credit cost is shown before image and video generation.
- Video credits are reserved once per unique request.
- Successful jobs finalize the reservation.
- API, moderation, and safety failures automatically refund the reservation.
- Personal Google API mode bypasses Nanode credits.

Current credit packages are listed at [nanode.tech/pricing](https://nanode.tech/pricing).

## Supported by Google Cloud for Startups

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/5/51/Google_Cloud_logo.svg" width="200" alt="Google Cloud">
</p>

Nanode is supported by the **Google Cloud for Startups** program. Its cloud credits help us operate the AI infrastructure behind Nanode and continue developing the open-source Blender add-on. Thank you to Google Cloud for supporting independent creators and open-source tools.

## Feedback and Support

- [Open a GitHub issue](https://github.com/Kovname/nano-banana-render/issues)
- Use the in-addon feedback controls
- Email [contact@nanode.tech](mailto:contact@nanode.tech)

## License

Nanode AI Render Engine is open-source software licensed under [GPL-3.0](LICENSE). Google model availability, regional restrictions, pricing, and API behavior are controlled by Google and can change during preview periods.

<div align="center">

Built by [Kovname](https://github.com/Kovname)

[Star](https://github.com/Kovname/nano-banana-render) |
[Download](https://github.com/Kovname/nano-banana-render/releases) |
[Website](https://nanode.tech)

</div>
