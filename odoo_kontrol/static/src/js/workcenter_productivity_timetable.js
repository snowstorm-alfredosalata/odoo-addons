odoo.define('odoo_kontrol.workcenter_productivity_timetable', function (require) {
'use strict';

var core = require('web.core');
var framework = require('web.framework');
var stock_report_generic = require('stock.stock_report_generic');

var QWeb = core.qweb;
var _t = core._t;


var WorkcenterProductivityTimetable = stock_report_generic.extend({
    events: {

    },

    init: function(parent, action) {
        this.actionManager = parent;
        this.andon_id = action.context.andon_id
        this.options = {period: 'days', offset: 0}
        return this._super.apply(this, arguments);
    },


    get_html: function() {
        var self = this;
        return this._rpc({
                model: 'mrp.andon',
                method: 'get_html',
                args: [self.andon_id, self.options],
                context: this.given_context,
            })
            .then(function (result) {
                self.data = result;
                self.options = result.options
            });
    },
    set_html: function() {
        var self = this;
        return this._super().then(function () {
            self.$('.o_content').html(self.data.html);
            self.renderSearch();
            self.update_cp();
            self.render_chart()

            if (self.options.auto_refresh > 0)
                setInterval(function() {self.reload();}, self.options.auto_refresh);
        });
    },
    render_html: function(event, $el, result){
        $el.after(result);
        this._reload_report_type();
    },
    update_cp: function () {
        var status = {
            cp_content: {
                $buttons: this.$buttonPrint,
                $searchview_buttons: this.$searchView
            },
        };
        return this.updateControlPanel(status);
    },
    renderSearch: function () {
        self = this

        this.$searchView = $();
        this.$buttonPrint = $(QWeb.render("ProductivityTimetable.buttons", {'options': self.options}))
        

        var $week = this.$buttonPrint.find('#week')
        $week.click(function () {
            self.options.period = 'weeks'
            self.options.offset = 0
            self.reload()
        })

        var $day = this.$buttonPrint.find('#day')
        $day.click(function () {
            self.options.period = 'days'
            self.options.offset = 0
            self.reload()
        })

        var $back = this.$buttonPrint.find('#back')
        $back.click(function () {
            self.options.offset += 1
            self.reload()
        })

        var $forward = this.$buttonPrint.find('#forward')
        $forward.click(function () {
            self.options.offset -= 1
            self.reload()
        })
    },

    reload: function() {
        self = this
        this.$el.find('#timetable-canvas').css('opacity', '0');

        this._rpc({
            model: 'mrp.andon',
            method: 'get_html',
            args: [self.andon_id, self.options],
            context: self.given_context,
        }).then(function (result) {
            self.data.graph = result.graph
            self.options = result.options
            return self.render_chart()
        });
    },


    render_chart: function() {
        var self = this;
        var chartSeries = []
        var shapes = []
        
        var $oee_bar        = this.$el.find('#oee_bar')
        var $oee_wrapper        = this.$el.find('.timetable-oee-wrapper')
        var $oee_percentage = this.$el.find('#oee_percentage')
        var $subheader = this.$el.find('.timetable-subheader')
        var $timetable_legend = this.$el.find('.timetable-legend')

        $subheader.html(self.data.graph.from_date + " - " + self.data.graph.to_date)
        
        const reducer = (accumulator, currentValue) => accumulator + currentValue.oee;
        var oee = 0
        
        $.each(self.data.graph.workcenter_ids, function(key, wc) { oee += wc.oee })
        
        oee = Math.round(oee/self.data.graph.workcenter_ids.length)
        
        if (isNaN(oee))
            $oee_wrapper.addClass('hidden')
        else {
            $oee_bar.css("width", oee + "%")
            $oee_percentage.html("OEE: " + oee + "%")
            $oee_wrapper.removeClass('hidden')
        }

        $oee_bar.removeClass(['bg-warning', 'bg-danger', 'bg-info', 'bg-success'])
        if (oee < 50) {
            $oee_bar.addClass('bg-danger')
        } else if (oee < 75) {
            $oee_bar.addClass('bg-warning')
        } else if (oee < 85)  {
            $oee_bar.addClass('bg-info')
        } else {
            $oee_bar.addClass('bg-success')
        }
        
        $timetable_legend.html("")
        $.each(self.data.graph.legend, function(key, l) {
            if (l.color)
                $timetable_legend.append($('<div class="timetable-legend-item"><div class="item-color" style="background-color:' + l.color + '"></div><div class="item-label">' + l.name + '</div></div>'))
        })

        var layout = {
            font: {
                family: 'Roboto',
                size: 12,
                color: '#7f7f7f',
            },
            margin: {l: 110, r: 0, t: 0, b: 0},
            grid: {
                rows: self.data.graph.workcenter_ids.length,
                columns: 1,
                pattern: 'independent',
                roworder: 'bottom to top'
            },

            shapes: shapes,
            autosize: true,
            hoverlabel: { bgcolor: "#FFF" },
            hovermode:'closest',
            width: 600,
            height: 60*self.data.graph.workcenter_ids.length,
        };

        var wc_index = 1
        var step = 1/self.data.graph.workcenter_ids.length
        $.each(self.data.graph.workcenter_ids, function(key, wc) {
            if (wc_index == 1) {
                layout["yaxis"] = {
                    domain: [(wc_index-1)*step, (wc_index)*step],
                    automargin: true,
                    fixedrange: true,
                    showgrid: true,
                    zeroline: false,
                    tickfont: {
                        family: 'Roboto, Odoo Unicode Support Noto, sans-serif',
                        size: 18,
                        color: wc.working_state == 'normal' ? 'black' : wc.working_state == 'done' ? 'green' : 'red'
                    },
                    tickwidth: 2,
                }
                layout["xaxis"] = {
                    zeroline: false,
                    automargin: true,
                    range: [self.data.graph.from_date, self.data.graph.to_date],
                }
            }
            else {
                layout["yaxis" + wc_index.toString()] = {
                    domain: [(wc_index-1)*step, (wc_index)*step],
                    automargin: true,
                    fixedrange: true,
                    showgrid: true,
                    zeroline: false,
                    tickfont: {
                        family: 'Roboto, Odoo Unicode Support Noto, sans-serif',
                        size: 18,
                        color: wc.working_state == 'normal' ? 'black' : wc.working_state == 'done' ? 'green' : 'red'
                    },
                    tickwidth: 2,
                }

            }
            
            $.each(wc.loss_ids, function(i, loss) {
                chartSeries.push({
                    type: 'scattergl',
                    x: [loss.date_start, loss.date_end],
                    y: [wc.name, wc.name],
                    yaxis: "y" + wc_index.toString(),
                    xaxis: "x",
                    mode: 'lines+markers',
                    hovertemplate: "<b>Inizio:</b> " + loss.date_start + "<br> <b>Fine:</b> "  + loss.date_end + "<br> <extra></extra>",
                    showlegend: false,
                    marker: {
                        width: 0,
                        color: '#ffffff00'
                    },
                    line: {
                        color: loss.color,
                        width:50
                    },
                })
            });
            wc_index += 1

        });
        
        this.$graphArea = this.$el.find('#timetable-canvas')
        this.$graphArea.html("")

        if(chartSeries.length >= 1) {
            Plotly.newPlot(self.$graphArea[0], chartSeries, layout, {displaylogo: false, displayModeBar: false});
    
            setTimeout(function () {
                Plotly.relayout(self.$graphArea[0], {width: self.$graphArea.width(), height: self.$graphArea.height()})
                self.$graphArea.css('opacity', '1')
            }, 10)
        } else {
            this.$graphArea.html($(QWeb.render("ProductivityTimetable.nodata", {})))
            this.$graphArea.css('opacity', '1');
        }
            

    },
});

core.action_registry.add('workcenter_productivity_timetable', WorkcenterProductivityTimetable);
return WorkcenterProductivityTimetable;

});