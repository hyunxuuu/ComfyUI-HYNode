import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
	name: "hynode.CSVSwitch",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "CSVSwitch") return;
        
        const origConfigure = nodeType.prototype.configure;
        nodeType.prototype.configure = function (data) {
            const csv_name_line = data?.properties?.csv_name_line ?? 0;

            if (data) {
                data.widgets_values = [];
                data.properties = {};
                data.properties.csv_name_line = csv_name_line;
            }

            this._csvCacheText = undefined;
            this._csvInflight = false;

            api.fetchApi("/hynode/CSVSwitch/configure", {
                method: "POST",
                body: JSON.stringify({
                    node_id: this.id,
                }),
            }).catch(err => console.error(err));

            return origConfigure.apply(this, arguments);
        };

		const origOnConnectionsChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function (side, slot, connect, link_info, output) {
            // console.log("[hynode] onConnectionsChange");

            if (side === 1 && this.inputs[slot]?.name === "csv_text") {
                const up = this.getInputNode(slot);
                const k = link_info?.origin_slot ?? 0;
                const upWidget = up?.widgets?.[k];
                let csv_text = ""

                if (connect) {
                    csv_text = upWidget?.value ?? up?.widgets_values?.[k] ?? "";
                }

                api.fetchApi("/hynode/CSVSwitch/csv_text/onConnectionsChange_onSelected", {
                    method: "POST",
                    body: JSON.stringify({
                        node_id: this.id,
                        connect: connect,
                        csv_text: csv_text,
                        default_line: this.properties.csv_name_line ?? 0,
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "Success") {
                        const widget = this.widgets?.find(w => w.name === "csv_name");
                        widget.options.values = data.values;
                        widget.value = data.values[data.csv_name_line] ?? "";

                        this.properties.csv_name_line = data.csv_name_line;

                        this.outputs?.forEach((o, i) => {
                            o.label = data.labels[i] ?? `out_${i + 1}`;
                            o.name = data.names[i] ?? `None`;
                        });
                        
                        this.size = this.computeSize();
                        this.setDirtyCanvas(true, true);
                        app.canvas.draw(true, true);

                        // console.log("[hynode] w.options.values:", widget.options.values);
                        // console.log("[hynode] w.value:", widget.value);
                    }
                    else if (data.status === "Failed") {
                        app.extensionManager.toast.add({
                            severity: "error",
                            summary: "CSVSwitch",
                            detail: data.message,
                            life: 8000,
                        });
                        return;
                    }
                })
                .catch(err => console.error(err));
            }

            if (origOnConnectionsChange) {
                origOnConnectionsChange.apply(this, arguments);
            }
        };

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            // console.log("[hynode] onNodeCreated");
            
            if (this.widgets?.find(item => item.name === "csv_name")) {
                const w = this.widgets?.find(item => item.name === "csv_name");
                const origCallback = w.callback;

                w.callback = (...args) => {
                    const line = w.options.values.indexOf(args[0]);

                    this.properties.csv_name_line = line

                    api.fetchApi("/hynode/CSVSwitch/csv_name/onNodeCreated", {
                        method: "POST",
                        body: JSON.stringify({
                            node_id: this.id,
                            line,
                        })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data && data.status === "Success") {
                            this.outputs?.forEach((o, i) => {
                                o.name = data.names[i] ?? `NONE`;
                            });
                    
                            this.size = this.computeSize();
                            this.setDirtyCanvas(true, true);
                            app.canvas.draw(true, true);
                        }
                    })
                    .catch(err => console.error(err));

                    if (origCallback) {
                        origCallback.apply(this, args);
                    }
                };
            }

            if (origOnNodeCreated) {
                origOnNodeCreated.apply(this, arguments);
            }
        };

        const origOnSelected = nodeType.prototype.onSelected;
        nodeType.prototype.onSelected = function () {
            console.log("[hynode] onSelected");

            const slot = this.inputs?.findIndex(i => i.name === "csv_text");
            const up = this.getInputNode(slot);
            const k = this.getInputLink(slot)?.origin_slot ?? 0;
            const csv_text = up?.widgets?.[k]?.value ?? up?.widgets_values?.[k] ?? "";

            if (up != null && csv_text !== this._csv_text) {
                this._csv_text = csv_text;
                api.fetchApi("/hynode/CSVSwitch/csv_text/onConnectionsChange_onSelected", {
                    method: "POST",
                    body: JSON.stringify({
                        node_id: this.id,
                        connect: true,
                        csv_text,
                        default_line: this.properties.csv_name_line ?? 0,
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "Success") {
                        const widget = this.widgets?.find(w => w.name === "csv_name");
                        widget.options.values = data.values;

                        if (widget.value == (data.values[data.csv_name_line] ?? "")) {
                            data.values[data.csv_name_line] = data.values[data.csv_name_line] + " ";
                        }
                        widget.value = data.values[data.csv_name_line];

                        this.size = this.computeSize();
                        this.setDirtyCanvas(true, true);
                        app.canvas.draw(true, true);

                        this.outputs?.forEach((o, i) => {
                            o.label = data.labels[i] ?? `out_${i + 1}`;
                            o.name = data.names[i] ?? `NONE`;
                        });
                        
                        this.size = this.computeSize();
                        this.setDirtyCanvas(true, true);
                        app.canvas.draw(true, true);

                        // console.log("[hynode] w.options.values:", widget.options.values);
                        // console.log("[hynode] w.value:", widget.value);
                    }
                    else if (data.status === "Failed") {
                        app.extensionManager.toast.add({
                            severity: "error",
                            summary: "CSVSwitch",
                            detail: data.message,
                            life: 8000,
                        });
                        return;
                    }
                })
                .catch(err => console.error(err));
            }

            if (origOnSelected) {
                origOnSelected.apply(this, arguments);
            }
        };
	},
})
