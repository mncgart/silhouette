# Silhouette

This repository provides a sample ComfyUI workflow for turning a single image into a video. The workflow is inspired by the "Veo 3" image-to-video approach and can be loaded directly in ComfyUI.

## Workflow File

The workflow JSON is located at `workflows/veo3_image_to_video.json`.

## Usage

1. Install [ComfyUI](https://github.com/comfyanonymous/ComfyUI).
2. Place the workflow file inside your ComfyUI `workflows` directory.
3. Start ComfyUI and load `veo3_image_to_video.json`.
4. Update the nodes to point to your input image, model checkpoint, and desired output path.
5. Run the workflow to generate a short video based on the input image.

Ensure that FFmpeg is installed so the `VideoCombine` node can create the final video file.
