odoo.define('cloud_base_documents.documents_kanban_controller', function (require) {
"use strict";
    
    var DocumentsKanbanController = require('documents.DocumentsKanbanController');

    DocumentsKanbanController.include({
        custom_events: _.extend({}, DocumentsKanbanController.prototype.custom_events, {
            download_cloud: '_onDownloadCloud',
        }),
        _onDownloadCloud: function(ev) {
            // The method to trigger single file from clouds
            ev.stopPropagation();
            window.location = '/web/cloud_content/' + ev.data.resID;
        },
        _onDownload: function (ev) {
            // re-write to make possible download of cloud file
            this._super.apply(this, arguments);
        },
    });

    return DocumentsKanbanController

});
