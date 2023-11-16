odoo.define('binaryImageModal.FieldBinaryImage', function (require) {
"use strict";

var core = require('web.core');
var DocumentViewer = require('mail.DocumentViewer');
var basic_fields = require('web.basic_fields');
var FieldBinaryImage = basic_fields.FieldBinaryImage;

function priority (f) {
    if (f == 'image_variant') {
        return 300
    } else if (f == 'image') {
        return 100
    } else {
        return 0
    }
 }

var FieldBinaryImage = FieldBinaryImage.include({
    template: 'FieldBinaryImage',

    /**
     * @override
     */
    events: _.extend({}, FieldBinaryImage.prototype.events, {
        'click img': function () {
            if (this.mode === "readonly") {
                this._onAttachmentView();
            }
        },
    }),

    _onAttachmentView: function (ev) {
        if ((this.model == 'product.product') && (this.recordData.product_tmpl_id)) {
            this._onAttachmentViewProduct(ev)
        } else {
            this._onAttachmentViewGeneric(ev)
        }

    },

    _onAttachmentViewGeneric: function (ev) {
        self = this

        this._rpc({
            model: 'ir.attachment',
            method: 'search_read',
            domain: [['res_model', '=', this.model], ['res_id', '=', this.res_id], ['res_field', 'in', ['image', self.name]]],
            fields: ['id', 'name', 'res_name', 'mimetype', 'type', 'url', 'res_field'],
            limit: 2
        }).then(function (atts) {
            if (!atts.length) {
                return
            } else {
                console.log(atts)
                atts = atts.sort(function (a, b) {
                    return priority(b.res_field) - priority(a.res_field)
                });
            }            

            var _att = atts[0]
            var att = [{
                "filename": _att.res_name,
                "id": _att.id,
                "​​main": true,
                "mimetype": _att.mimetype,
                "name": _att.name,
                "type": ((_att.type == 'url') ? 'url' : 'image'),
                "url": ((_att.type == 'url') ? _att.url : '/web/image/'+_att.id),
                }];
            
            var attachmentViewer = new DocumentViewer(self, att, _att.id);
            attachmentViewer.appendTo($('body'));
        });
    },

    _onAttachmentViewProduct: function (ev) {
        self = this
        
        this._rpc({
            model: 'ir.attachment',
            method: 'search_read',
            domain: [
                     '|', 
                        '&',
                            ['res_model', '=', 'product.product'], 
                            '&',
                                ['res_id', '=', this.res_id],
                                ['res_field', '=', 'image_variant'],
                        '&',
                            ['res_model', '=', 'product.template'], 
                            '&', 
                                ['res_id', '=', this.recordData.product_tmpl_id.res_id],
                                ['res_field', '=', 'image']
                    ],
            fields: ['id', 'name', 'res_name', 'mimetype', 'type', 'url', 'file_size'],
            limit: 4,
        }).then(function (atts) {
            if (!atts.length) {
                return
            } else {
                console.log(atts)
                atts = atts.sort(function (a, b) {
                    return priority(b.name) - priority(a.name)
                });
                console.log(atts)
            }

            var _att = atts[0]
            atts = []
            var att = [{
                "filename": _att.res_name,
                "id": _att.id,
                "​​main": true,
                "mimetype": _att.mimetype,
                "name": _att.name,
                "type": ((_att.type == 'url') ? 'url' : 'image'),
                "url": ((_att.type == 'url') ? _att.url : '/web/image/'+_att.id),
                }];
            
            var attachmentViewer = new DocumentViewer(self, att, _att.id);
            attachmentViewer.appendTo($('body'));
        });
    },
});
});

