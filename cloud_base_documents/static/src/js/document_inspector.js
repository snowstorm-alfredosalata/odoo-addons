odoo.define('cloud_base_documents.document_inspector', function (require) {
"use strict";
    
    var core = require('web.core');
    var fieldRegistry = require('web.field_registry');
    var DocumentsInspector = require('documents.DocumentsInspector');
    var qweb = core.qweb;

    DocumentsInspector.include({
        init: function(parent, params) {
            // re-write to make cloud files not image
            this._super.apply(this, arguments);
            for (const resID of params.recordIDs) {
                var record = _.findWhere(params.state.data, {res_id: resID});
                if (record) {
                    if (record.data.cloud_key) {
                        this.recordsData[record.id].isGif = false;
                        this.recordsData[record.id].isImage = false;
                        this.recordsData[record.id].isCloud = true;
                    };
                };
            };
        },
        _updateButtons: function () {
            // re-write to make possible multi upload of cloud files
            this._super.apply(this, arguments);
            var cloudFiles = _.some(this.records, function (record) {
                return record.data.cloud_key && record.data.mimetype !== 'application/octet-stream' && 
                       record.data.mimetype !== 'special_cloud_folder';
            });
            if (cloudFiles) {
                this.$('.o_inspector_download').prop('disabled', false);
            };
        },
        _onDownload: function () {
            // Re write to trigger different donwload if it is a cloud file
            var cloudFiles = _.some(this.records, function (record) {
                return record.data.cloud_key && record.data.mimetype !== 'application/octet-stream' && 
                       record.data.mimetype !== 'special_cloud_folder';
            });
            if (cloudFiles && this.records.length === 1) {
                this.trigger_up('download_cloud', {
                    resID: this.records[0].data.attachment_id.res_id,
                });
            }
            else {
                this._super.apply(this, arguments);
            }           
        },
        _renderField: function (fieldName, options) {
            // re-write to make cloud url readonly
            var record = this.records[0];
            if (fieldName == "url" && record.data.cloud_key) {
                var $row = $(qweb.render('documents.DocumentsInspector.infoRow'));
                var $label = $(qweb.render('documents.DocumentsInspector.fieldLabel', {
                    icon: options.icon,
                    label: options.label || record.fields[fieldName].string,
                    name: fieldName,
                }));
                $label.appendTo($row.find('.o_inspector_label'));
                var FieldWidget = fieldRegistry.get("link_button");
                var fieldWidget = new FieldWidget(this, fieldName, record, options);
                const prom = fieldWidget.appendTo($row.find('.o_inspector_value')).then(function() {
                    var elem = $('.o_inspector_value').find('.o_field_widget');
                    elem.attr('id', fieldName);
                    elem.addClass("cloud_link_docs");
                });
                $row.insertBefore(this.$('.o_inspector_fields tbody tr.o_inspector_divider'));
                return prom;
            }
            else {
                return this._super(fieldName, options);
            }            
        },
    });

    return DocumentsInspector

});
