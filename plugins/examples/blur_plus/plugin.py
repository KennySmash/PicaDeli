from plugins.vx import register


def execute(image, radius: float = 2.0):
    # placeholder: real implementation will use node_engine GPU path
    return image


def register_plugin():
    register(
        {
            "name": "blur_plus",
            "version": "1.0.0",
            "type": "node",
            "entrypoint": "plugins.examples.blur_plus.plugin.execute",
        }
    )
