WEB_DIRECTORY = "./web"

from comfy_api.latest import ComfyExtension
from .src.CSVSwitch import CSVSwitch

class MyExtension(ComfyExtension):
    async def get_node_list(self):
        return [CSVSwitch]

async def comfy_entrypoint():
    return MyExtension()
    