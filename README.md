# ComfyUI-ResizeDimensions

A single ComfyUI custom node — **Resize Dimensions (W/H)** — that computes
latent-safe width/height from an image's aspect ratio (or fixed sizes) and can
also output a matching empty **LATENT** batch, so you can skip a separate Empty
Latent Image node. It does **not** resample the image; the image is read only for
its aspect ratio.

## Install

**Via ComfyUI-Manager:** *Install via Git URL* → paste this repo's URL, then restart.

**Manual:**
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/normbarrette-arch/ComfyUI-ResizeDimensions.git
```
Restart ComfyUI. The node appears under **image/size** as *Resize Dimensions (W/H)*.

## Node: Resize Dimensions (W/H)

A `mode` selector chooses one of three sizing functions; only the active one is
output. Both outputs are snapped to `round_to`.

**Inputs**
- `image` — source image (only its aspect ratio is read, for the edge modes).
- `mode`:
  - `long edge` — pin the **longer** source side to `edge_length`; the other side scales (aspect preserved).
  - `short edge` — pin the **shorter** source side to `edge_length`; the other side scales (aspect preserved).
  - `set size A` — output exactly `width_a` × `height_a`.
  - `set size B` — output exactly `width_b` × `height_b`.
- `edge_length` — target for the long/short edge modes.
- `width_a` / `height_a`, `width_b` / `height_b` — exact sizes for the set-size modes.
- `round_to` — snap both outputs to this multiple (`8`/`16`/`32`/`64`/`1`).
- `latent_type` — latent channel count for the LATENT output: `SD3 / Flux / Qwen (16ch)`
  or `SDXL / SD1.5 (4ch)`. **Must match your model.**
- `batch_size` — number of empty latents in the output batch.

**Outputs**
- `width` (INT), `height` (INT) — the single selected pair.
- `latent` (LATENT) — an empty (zeros) batch at the computed size. Leave it
  unconnected if you only need width/height.

Every output is snapped to `round_to`, so even a typed `set size` value is nudged
to the nearest multiple — set `round_to = 1` for an exact odd value (note the
latent floor-divides by 8, so keep `round_to` at 8+ for an exact size match).

## License

MIT — see [LICENSE](LICENSE).
