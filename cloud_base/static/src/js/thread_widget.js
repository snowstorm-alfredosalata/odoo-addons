odoo.define('cloud_base.thread', function (require) {
"use strict";
    
    var core = require('web.core');
    var Thread = require('mail.widget.Thread');
    var DocumentViewer = require('mail.DocumentViewer');
    var _t = core._t;

    Thread.include({
        events: _.extend({}, Thread.prototype.events, {
            "click .o_attachment_view_cloud": "_onOpenCloudLink",
            "click .o_attachment_download_from_cloud": "_onFileCloudDownload",
            "click .o_cloud_preview": "_onPreviewCloud",
        }),
        _onOpenCloudLink: function(event) {
            // The method to open cloud link
            var self = this;
            var attachmentID = parseInt($(event.currentTarget).data('id'));
            this._rpc({
                model: "ir.attachment",
                method: 'open_cloud_link',
                args: [[attachmentID]],
            }).then(function (action) {
                if (action) {self.do_action(action);}
                else {self.do_warn(_t('Odoo cannot find the url'));}
            });             
        },
        _onFileCloudDownload: function (event) {
            // The method to request cloud for binary
            event.stopPropagation();
            var self = this;
            var attachmentID = parseInt($(event.currentTarget).data('id'));
            this._rpc({
                model: "ir.attachment",
                method: 'upload_attachment_from_cloud_ui',
                args: [[attachmentID]],
            }).then(function (action) {
                self.do_action(action);
            });            
        },
        _onPreviewCloud: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            var activeAttachmentID = $(ev.currentTarget).data('id');
            if (activeAttachmentID) {
                var attachmentViewer = new DocumentViewer(this, this.attachments, activeAttachmentID);
                attachmentViewer.appendTo($('body'));
            }
        },


    });

    return Thread

});
