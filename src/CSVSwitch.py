from comfy_api.latest import io
from aiohttp import web
from server import PromptServer
import enum
import math
from .lib.CSVLexer import csv_lexer








OUTNUM = 8

type_map = {
    "str": "STRING",
    "int": "INT",
    "float": "FLOAT",
    "bool": "BOOLEAN",
}

class CSVStatus:
    def __init__(self):
        self.list = []
        self.line = None
        self.text = ""

csvStatus = {}

class CSVSwitch(io.ComfyNode):
    @classmethod
    def validate_inputs(cls, csv_name):
        return True

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="CSVSwitch",
            display_name="CSVSwitch",
            category="HYNode",
            hidden=[io.Hidden.unique_id],
            inputs=[
                io.String.Input(
                    "csv_text",
                    force_input=True
                ),
                io.Combo.Input(
                    "csv_name",
                    options=[""],
                    default="",
                ),
            ],
            outputs=[
                io.AnyType.Output(f"out_{i + 1}")
                for i in range(OUTNUM)
            ]
        )

    @classmethod
    def execute(cls, csv_text, csv_name) -> io.NodeOutput:
        node_id = str(cls.hidden.unique_id)
        results = [None] * OUTNUM
        if node_id not in csvStatus:
            raise RuntimeError("node_id is null!")
            
        csvStatus[node_id].text = csv_text
        csvStatus[node_id].list = []
        ret = csv_lexer(csv_text, csvStatus[node_id].list)

        if ret != "":
            csvStatus[node_id].line = None
            raise RuntimeError(f"\n{ret}")
        # print("node_id:", node_id, "list:", csvStatus[node_id].list)
        
        if 1 + csvStatus[node_id].line < len(csvStatus[node_id].list):
            for i in range(OUTNUM):
                if 1 + i < len(csvStatus[node_id].list[1 + csvStatus[node_id].line]):
                    results[i] = csvStatus[node_id].list[1 + csvStatus[node_id].line][1 + i]
                else:
                    break

        return io.NodeOutput(*results)
        







        
@PromptServer.instance.routes.post("/hynode/CSVSwitch/configure")
async def CSVSwitch_reset(request):
    global csvStatus

    json_data = await request.json()
    node_id = json_data.get("node_id")

    if node_id is None:
        csvStatus.clear()
    else:
        csvStatus.pop(node_id, None)

    return web.json_response({"status": "Success"})

@PromptServer.instance.routes.post("/hynode/CSVSwitch/csv_text/onConnectionsChange_onSelected")
async def CSVSwitch_csv_text_onConnectionsChange_onSelected(request):
    global csvStatus

    json_data = await request.json()
    node_id = json_data.get("node_id")
    connect = json_data.get("connect")
    csv_text = json_data.get("csv_text")
    default_line = json_data.get("default_line")

    # print("node_id:", type(node_id).__name__, node_id)
    # print("connect:", type(connect).__name__, connect)
    # print("csv_text:", type(csv_text).__name__, csv_text)
    # print("default_line:", type(default_line).__name__, default_line)

    values = []
    labels = []
    names = []
    csv_name_line = 0

    if connect:
        if node_id not in csvStatus:
            csvStatus[node_id] = CSVStatus()

        if csv_text != csvStatus[node_id].text:
            csvStatus[node_id].text = csv_text
            csvStatus[node_id].list = []

            ret = csv_lexer(csv_text, csvStatus[node_id].list)
            if ret != "":
                csvStatus[node_id].line = None
                return web.json_response({
                    "status": "Failed",
                    "message": ret,
                })
            # print("node_id:", node_id, "list:", csvStatus[node_id].list)

        values = [item[0] for item in csvStatus[node_id].list[1 : ]]

        if len(csvStatus[node_id].list) > 0:
            for value in csvStatus[node_id].list[0][1 : OUTNUM + 1]:
                labels.append(value)

        if len(csvStatus[node_id].list) > 1:
            csvStatus[node_id].line = 0
            csv_name_line = 0

            if 1 + default_line < len(csvStatus[node_id].list):
                csvStatus[node_id].line = default_line
                csv_name_line = default_line

            for value in csvStatus[node_id].list[1 + csv_name_line][1 : OUTNUM + 1]:
                # names.append(f" [Type:{type_map.get(type(value).__name__, type(value).__name__)}] [Length:{len(str(value))}] [Value:{value}]")
                names.append(f"{value}\nType: {type_map.get(type(value).__name__, type(value).__name__)}\nLength: {len(str(value))}")
    else:
        csvStatus.pop(node_id, None)

    # print("values:", values)
    # print("labels:", labels)
    # print("names:", names)
    # print("csv_name_line:", csv_name_line)

    return web.json_response({
        "status": "Success",
        "values": values,
        "labels": labels,
        "names": names,
        "csv_name_line": csv_name_line,
    })
    
@PromptServer.instance.routes.post("/hynode/CSVSwitch/csv_name/onNodeCreated")
async def CSVSwitch_csv_name_onNodeCreated(request):
    global csvStatus

    json_data = await request.json()
    node_id = json_data.get("node_id")
    line = json_data.get("line")

    # print("node_id:", node_id)
    # print("line:", line)

    csvStatus[node_id].line = line

    names = []
    
    for value in csvStatus[node_id].list[1 + line][1 : OUTNUM + 1]:
        names.append(f"{value}\nType: {type_map.get(type(value).__name__, type(value).__name__)}\nLength: {len(str(value))}")

    # print("names:", names)

    return web.json_response({
        "status": "Success",
        "names": names,
    })
