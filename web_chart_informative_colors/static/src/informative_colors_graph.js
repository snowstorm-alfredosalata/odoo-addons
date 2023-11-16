/** @odoo-module **/

import { registry } from "@web/core/registry";

import { graphView } from "@web/views/graph/graph_view";

import { GraphModel } from "@web/views/graph/graph_model";
import { GraphController } from "@web/views/graph/graph_controller";
import { GraphRenderer } from "@web/views/graph/graph_renderer";

export class InformativeColorsGraphModel extends GraphModel {

    _getData(dataPoints) {
        var data = super._getData(dataPoints);
        console.log(dataPoints);
        console.log(data);
        return data;
    }
}

export class InformativeColorsGraphController extends GraphController {

    onGraphClicked(domain) {
        return super.onGraphClicked(domain);
    }
}



export class InformativeColorsGraphRenderer extends GraphRenderer {

    onGraphClicked(ev) {
        console.log(ev)
        return super.onGraphClicked(ev);
    }

    getBarChartData() {
        var barChartData = super.getBarChartData();
        //console.log(barChartData);
        return barChartData;
    }
}

export const informativeColorsGraphView = {
    ...graphView,
    Model: InformativeColorsGraphModel,
    Controller: InformativeColorsGraphController,
    Renderer: InformativeColorsGraphRenderer
};

registry.category("views").add("informative_colors_graph", informativeColorsGraphView);
