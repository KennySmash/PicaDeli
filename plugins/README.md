# Plugin SDK (Stub)

- Global registry: `vx.register({...})`
- Minimal required fields: `name`, `version`, `type`, `entrypoint`.
- Example plugin: `plugins/examples/blur_plus/plugin.py` with `register_plugin()`.

Discovery (future): CLI/UI will import modules and call `register_plugin()`.
