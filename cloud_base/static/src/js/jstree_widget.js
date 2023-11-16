odoo.define('cloud_base.jstree_widget', function (require) {
"use strict";

    var registry = require('web.field_registry');
    var core = require('web.core');
    var AbstractField = require('web.AbstractField');
    var qweb = core.qweb;
    var basicFields = require('web.basic_fields');

    var jsTreeWidget = AbstractField.extend({
        supportedFieldTypes: ['char'],
        resetOnAnyFieldChange: false,
        jsLibs: [
            '/cloud_base/static/lib/jstree/jstree.js',
        ],
        cssLibs: [
            '/cloud_base/static/lib/jstree/themes/default/style.css',
        ],
        events: _.extend({}, AbstractField.prototype.events, {
            'click #createJsTreeNode': '_onAddNode',
            'click #editJsTreeNode': '_onEditNode',
            'click #deleteJsTreeNode': '_onDeleteNode',
        }),
        _renderEdit: function () {
            // Re-write to parse jstree lib
            var self = this;
            var template = qweb.render('jsTreeWidget', {"mode": self.mode});
            self.$el.html(template);
            var cur_data = []
            if (self.value) {
                cur_data = eval(self.value)
            };
            var ref = self.$('#jsTreeContainer').jstree({
                'core' : {
                    "check_callback" : true,
                    'data': cur_data,
                },
                "plugins" : [
                    "contextmenu",
                    "dnd",
                    "state",
                    "unique",
                ],
            });
            // Manage any change to register it
            self.$('#jsTreeContainer').on("rename_node.jstree", self, function (event, data) {
                // when created, a node is always renamed
                self._onChangeTree(event, data);
            });
            self.$('#jsTreeContainer').on("move_node.jstree", self, function (event, data) {
                self._onChangeTree(event, data);
            });
            self.$('#jsTreeContainer').on("delete_node.jstree", self, function (event, data) {
                self._onChangeTree(event, data);
            });
            self.$('#jsTreeContainer').on("copy_node.jstree", self, function (event, data) {
                self._onChangeTree(event, data);
            });
        },
        _renderReadonly: function () {
            // Re-write to parse jstree lib
            var self = this;
            var template = qweb.render('jsTreeWidget', {"mode": self.mode});
            self.$el.html(template);
            var cur_data = []
            if (self.value) {
                cur_data = eval(self.value)
            };
            var ref = self.$('#jsTreeContainer').jstree({
                'core' : {
                    "themes" : { "stripes" : false },
                    'data': cur_data,
                },
            });
        },
        _onAddNode: function(event) {
            // The method to add a new node
            var self = this;
            var ref = self.$('#jsTreeContainer').jstree(true),
                sel = ref.get_selected();
            // To the UI purposes button serves to create only top level directories
            // if(sel.length) {
            //    sel = sel[0];
            //    sel = ref.create_node(sel);
            // }
            // else {
            //     sel = ref.create_node('#');
            // };
            sel = ref.create_node('#');
            if(sel) {
                ref.edit(sel);
            }
        },
        _onEditNode: function(event) {
            // The method to edit this node
            var self = this;
            var ref = self.$('#jsTreeContainer').jstree(true),
                sel = ref.get_selected();
            if(!sel.length) { return false; }
            sel = sel[0];
            ref.edit(sel);
        },
        _onDeleteNode: function(event) {
            // The method to delete this node
            var self = this;
            var ref = self.$('#jsTreeContainer').jstree(true),
                sel = ref.get_selected();
            if(!sel.length) { return false; }
            ref.delete_node(sel);
        },
        _onChangeTree:  function(event, data) {
            var self = this;
            var ref = self.$('#jsTreeContainer').jstree(true);
            var cur_data = JSON.stringify(ref.get_json());
            self._setValue(cur_data);
        },
    });

    registry.add('jsTreeWidget', jsTreeWidget);

});
