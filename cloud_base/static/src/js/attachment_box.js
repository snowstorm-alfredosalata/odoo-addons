odoo.define('cloud_base.attachment_box', function (require) {
"use strict";
    
    var core = require('web.core');
    var AttachmentBox = require('mail.AttachmentBox');
    var DocumentViewer = require('mail.DocumentViewer');
    var _t = core._t;

    AttachmentBox.include({
        events: _.extend({}, AttachmentBox.prototype.events, {
            "click .o_attachment_view_cloud": "_onOpenCloudLink",
            "click .o_open_cloud_folder": "_onOpenCloudFolder",
            "click .o_attachment_download_from_cloud": "_onFileCloudDownload",
            "click .o_cloud_preview": "_onPreviewCloud",
        }),
        init: function (parent, record, attachments) { 
            // Re-write to split attachments into synced and not synced
            this.cloudSynced = parent.cloudSynced;
            var sortedSyncAttachments = _.partition(attachments, function (att) {return att.cloud_key;});
            this.syncedList = sortedSyncAttachments[0].sort(
                (a,b) => (a.mimetype != 'special_cloud_folder' && b.mimetype == 'special_cloud_folder') ? 1: -1
            );
            attachments = sortedSyncAttachments[1];
            this._super(parent, record, attachments);      
        },
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
        _onOpenCloudFolder: function (event) {
            // The method to open the link related to this record
            var self = this;
            this._rpc({
                model: "ir.attachment",
                method: 'open_cloud_folder',
                args: [{
                    "res_model": self.currentResModel,
                    "res_id": self.currentResID,
                }],
            }).then(function (action) {
                if (action) {self.do_action(action);}
                else {self.do_warn(_t('The object is either not synced or the service is unavailable'));}
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
                var attachmentViewer = new DocumentViewer(this, this.syncedList, activeAttachmentID);
                attachmentViewer.appendTo($('body'));
            }
        },
    });

    return AttachmentBox

});
