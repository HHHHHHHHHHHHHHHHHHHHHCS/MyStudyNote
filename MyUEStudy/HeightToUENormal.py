from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def load_height_as_ue_meters(path: Path, z_scale_cm: float) -> np.ndarray:
    image = Image.open(path)
    data = np.asarray(image)

    if data.ndim == 3:
        rgb = data[..., :3].astype(np.float32)
        depth = rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722
    else:
        depth = data.astype(np.float32)

    if np.issubdtype(data.dtype, np.integer):
        max_value = float(np.iinfo(data.dtype).max)
        if max_value <= 255.0:
            raw_height = np.clip(depth / max_value, 0.0, 1.0) * 65536.0
        else:
            raw_height = depth
    else:
        raw_height = np.clip(depth, 0.0, 1.0) * 65536.0

    # UE Landscape height in centimeters:
    #   (Height16 - 32768) / 128 * ZScale
    height_cm = (raw_height - 32768.0) / 128.0 * z_scale_cm
    return (height_cm / 100.0).astype(np.float32)


def height_to_tangent_normal(
    height_m: np.ndarray,
    xy_scale_cm: float,
    strength: float,
    opengl: bool,
    method: str,
) -> np.ndarray:
    xy_m = xy_scale_cm / 100.0
    if xy_m <= 0.0:
        raise ValueError("xy_scale_cm must be greater than 0.")

    padded = np.pad(height_m, 1, mode="edge")
    top_left = padded[:-2, :-2]
    top = padded[:-2, 1:-1]
    top_right = padded[:-2, 2:]
    left = padded[1:-1, :-2]
    right = padded[1:-1, 2:]
    bottom_left = padded[2:, :-2]
    bottom = padded[2:, 1:-1]
    bottom_right = padded[2:, 2:]

    if method == "central":
        dzdx = (right - left) / (2.0 * xy_m)
        dzdy = (bottom - top) / (2.0 * xy_m)
    elif method == "sobel":
        dzdx = (
            (top_right + 2.0 * right + bottom_right)
            - (top_left + 2.0 * left + bottom_left)
        ) / (8.0 * xy_m)
        dzdy = (
            (bottom_left + 2.0 * bottom + bottom_right)
            - (top_left + 2.0 * top + top_right)
        ) / (8.0 * xy_m)
    else:
        raise ValueError(f"Unsupported normal method: {method}")

    nx = -dzdx * strength
    # UE uses DirectX normal maps: +Y points down in texture space.
    # OpenGL normal maps are the same result with the green channel flipped.
    ny = dzdy * strength if opengl else -dzdy * strength
    nz = np.ones_like(height_m, dtype=np.float32)

    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.dstack((nx / length, ny / length, nz / length))
    return np.clip(np.rint((normal * 0.5 + 0.5) * 255.0), 0, 255).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a heightmap to a UE/DirectX normal map.")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("-s", "--strength", type=float, default=1.0, help="Extra slope multiplier after UE scale reconstruction.")
    parser.add_argument("--xy-scale-cm", type=float, default=100.0, help="Landscape X/Y scale in centimeters per height sample.")
    parser.add_argument("--z-scale-cm", type=float, default=100.0, help="Landscape Z scale in centimeters.")
    parser.add_argument("--method", choices=("central", "sobel"), default="sobel", help="Gradient method used to derive the normal map.")
    parser.add_argument("--opengl", action="store_true", help="Output OpenGL green channel instead of UE/DirectX.")
    args = parser.parse_args()

    output = args.output
    if output is None:
        convention = "OpenGL" if args.opengl else "UE_DX"
        method_suffix = f"_{args.method.capitalize()}"
        suffix = f"Normal_{convention}{method_suffix}"
        output = args.input.with_name(f"{args.input.stem}_{suffix}.png")

    height_m = load_height_as_ue_meters(args.input, args.z_scale_cm)
    normal = height_to_tangent_normal(height_m, args.xy_scale_cm, args.strength, args.opengl, args.method)
    Image.fromarray(normal).save(output)
    print(output.resolve())


if __name__ == "__main__":
    main()
