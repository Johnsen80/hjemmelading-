import importlib
import os


class PluginManager:
    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.plugins = {}

    def load_plugins(self):
        """Dynamically load all plugins from the plugin directory."""
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                module_path = f"plugins.{module_name}"
                try:
                    module = importlib.import_module(module_path)
                    self.plugins[module_name] = module
                    print(f"Loaded plugin: {module_name}")
                except ImportError as e:
                    print(f"Failed to load plugin {module_name}: {e}")

    def execute_plugin(self, plugin_name, *args, **kwargs):
        """Execute a specific plugin by name."""
        plugin = self.plugins.get(plugin_name)
        if plugin and hasattr(plugin, "run"):
            return plugin.run(*args, **kwargs)
        else:
            print(f"Plugin {plugin_name} not found or missing 'run' method.")


if __name__ == "__main__":
    # Example usage
    plugin_manager = PluginManager("plugins")
    plugin_manager.load_plugins()
    plugin_manager.execute_plugin("example_plugin")
