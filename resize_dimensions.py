"""
Resize Dimensions (W/H) - a dimension calculator for latent sizing, with an
optional empty-latent output.

One node with three sizing functions; a 'mode' selector chooses which one is
active, and only that function's width/height pair is output. It also emits a
matching empty LATENT (zeros) at the computed size with a batch_size selector,
so a separate Empty Latent Image node isn't needed. It does not resample the
image.

Functions:
  - long edge / short edge : pin that edge of the source image to 'edge_length',
                             the other side scales to preserve aspect ratio.
  - set size A             : output exactly width_a x height_a.
  - set size B             : output exactly width_b x height_b.

The LATENT is built like the core EmptyLatentImage / EmptySD3LatentImage nodes;
'latent_type' picks the channel count (16 for SD3/Flux/Qwen, 4 for SD1.5/SDXL).
torch / comfy.model_management are imported lazily inside compute() so the module
imports with no heavy dependencies (keeps load + unit-testing light).

ComfyUI IMAGE tensors are shaped (Batch, Height, Width, Channels), so the source
height is image.shape[1] and the source width is image.shape[2].
"""

import math

# Matches ComfyUI's own nodes.py cap; avoids importing from the core module.
MAX_RESOLUTION = 16384

# Latent label -> channel count. 16ch matches EmptySD3LatentImage (SD3/Flux/Qwen);
# 4ch matches EmptyLatentImage (SD1.5/SDXL).
LATENT_TYPES = {
    "SD3 / Flux / Qwen (16ch)": 16,
    "SDXL / SD1.5 (4ch)": 4,
}


class ResizeDimensions:
    MODES = ["long edge", "short edge", "set size A", "set size B"]
    ROUND_OPTIONS = ["8", "16", "32", "64", "1"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mode": (cls.MODES,),
                "edge_length": ("INT", {"default": 1080, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                "width_a": ("INT", {"default": 1024, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                "height_a": ("INT", {"default": 1024, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                "width_b": ("INT", {"default": 1024, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                "height_b": ("INT", {"default": 576, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                "round_to": (cls.ROUND_OPTIONS, {"default": "8"}),
                "latent_type": (list(LATENT_TYPES.keys()),),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4096, "tooltip": "Number of empty latents in the batch."}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "LATENT")
    RETURN_NAMES = ("width", "height", "latent")
    FUNCTION = "compute"
    CATEGORY = "image/size"
    DESCRIPTION = (
        "Compute latent-safe width/height from an image's aspect ratio (or fixed "
        "sizes), and also output a matching empty LATENT batch so a separate Empty "
        "Latent Image node isn't needed. Pick a mode and a latent_type (16ch for "
        "SD3/Flux/Qwen, 4ch for SD1.5/SDXL). Does not resample the image."
    )

    def compute(self, image, mode, edge_length, width_a, height_a, width_b, height_b,
                round_to, latent_type, batch_size):
        src_h = int(image.shape[1])
        src_w = int(image.shape[2])
        multiple = max(1, int(round_to))

        if mode == "long edge":
            out_w, out_h = self._edge(src_w, src_h, edge_length, longer=True)
        elif mode == "short edge":
            out_w, out_h = self._edge(src_w, src_h, edge_length, longer=False)
        elif mode == "set size A":
            out_w, out_h = width_a, height_a
        elif mode == "set size B":
            out_w, out_h = width_b, height_b
        else:  # unreachable; keep dimensions sane just in case
            out_w, out_h = src_w, src_h

        out_w = self._snap(out_w, multiple)
        out_h = self._snap(out_h, multiple)

        latent = self._empty_latent(out_w, out_h, latent_type, batch_size)
        return (out_w, out_h, latent)

    @staticmethod
    def _empty_latent(width, height, latent_type, batch_size):
        """Build an empty latent batch like core EmptyLatentImage/EmptySD3LatentImage."""
        import torch
        import comfy.model_management

        channels = LATENT_TYPES.get(latent_type, 16)
        latent = torch.zeros(
            [batch_size, channels, height // 8, width // 8],
            device=comfy.model_management.intermediate_device(),
            dtype=comfy.model_management.intermediate_dtype(),
        )
        return {"samples": latent, "downscale_ratio_spacial": 8}

    @staticmethod
    def _edge(src_w, src_h, target, longer):
        """Pin the longer (or shorter) source side to target; scale the other."""
        if src_w <= 0 or src_h <= 0:
            return (target, target)
        # Which side gets pinned to target?
        width_is_pinned = (src_w >= src_h) if longer else (src_w <= src_h)
        if width_is_pinned:
            return (target, target * src_h / src_w)
        return (target * src_w / src_h, target)

    @staticmethod
    def _snap(value, multiple):
        """Round to the nearest multiple (ties go up), never below one multiple."""
        snapped = int(math.floor(float(value) / multiple + 0.5)) * multiple
        return snapped if snapped >= multiple else multiple


NODE_CLASS_MAPPINGS = {"RB_ResizeDimensions": ResizeDimensions}
NODE_DISPLAY_NAME_MAPPINGS = {"RB_ResizeDimensions": "Resize Dimensions (W/H)"}
