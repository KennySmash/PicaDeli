from __future__ import annotations

import traceback
from typing import Optional


class QtWgpuScene:
    """Minimal wgpu scene: clear color + triangle (if pipeline builds).

    This class is imported and used only if wgpu is installed.
    """

    def __init__(self, canvas):  # canvas: rendercanvas.qt.WgpuCanvas
        import wgpu
        import wgpu.backends.auto  # noqa: F401
        from wgpu.utils import get_default_device

        self.wgpu = wgpu
        self.canvas = canvas
        # Newer wgpu.utils.get_default_device() has no canvas arg
        try:
            self.device = get_default_device()
        except TypeError:
            # Older versions may still accept canvas
            self.device = get_default_device(canvas=canvas)  # type: ignore[arg-type]
        self.queue = self.device.queue

        self.pipeline = None
        self.vertex_buffer = None

        try:
            self._init_triangle_pipeline()
        except Exception:
            traceback.print_exc()
            # Pipeline optional; we can still clear screen.

        # Hook draw callback
        canvas.request_draw(self.draw_frame)

    def _init_triangle_pipeline(self):
        wgpu = self.wgpu
        # WGSL shader for a fullscreen triangle
        shader = self.device.create_shader_module(code="""
            @vertex
            fn vs_main(@builtin(vertex_index) v_idx : u32) -> @builtin(position) vec4f {
                var pos = array<vec2f, 3>(
                    vec2f(-1.0, -3.0),
                    vec2f(-1.0,  1.0),
                    vec2f( 3.0,  1.0)
                );
                let p = pos[v_idx];
                return vec4f(p, 0.0, 1.0);
            }
            @fragment
            fn fs_main() -> @location(0) vec4f {
                return vec4f(0.15, 0.18, 0.22, 1.0);
            }
        """)

        # Prefer asking the canvas; fall back to a common swapchain format
        try:
            format = self.canvas.get_preferred_format(self.device.adapter)
        except Exception:
            format = wgpu.TextureFormat.bgra8unorm

        self.pipeline = self.device.create_render_pipeline(
            layout="auto",
            vertex={
                "module": shader,
                "entry_point": "vs_main",
                "buffers": [],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list},
            fragment={
                "module": shader,
                "entry_point": "fs_main",
                "targets": [{"format": format}],
            },
        )

    def draw_frame(self):
        wgpu = self.wgpu
        current_texture = self.canvas.get_current_texture()
        view = current_texture.create_view()
        encoder = self.device.create_command_encoder()

        if self.pipeline is None:
            # simple clear pass
            render_pass = encoder.begin_render_pass(
                color_attachments=[{
                    "view": view,
                    "clear_value": (0.10, 0.12, 0.16, 1.0),
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                }]
            )
            render_pass.end()
        else:
            render_pass = encoder.begin_render_pass(
                color_attachments=[{
                    "view": view,
                    "clear_value": (0.05, 0.06, 0.08, 1.0),
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                }]
            )
            render_pass.set_pipeline(self.pipeline)
            render_pass.draw(3, 1, 0, 0)
            render_pass.end()

        self.queue.submit([encoder.finish()])
        try:
            current_texture.present()
        except Exception:
            pass
        self.canvas.request_draw()


def create_wgpu_scene(canvas) -> Optional[QtWgpuScene]:
    try:
        return QtWgpuScene(canvas)
    except Exception:
        traceback.print_exc()
        return None
