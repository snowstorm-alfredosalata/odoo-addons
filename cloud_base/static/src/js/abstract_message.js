odoo.define('cloud_base.abstract_message', function (require) {
"use strict";
    
    var AbstractMessage = require('mail.model.AbstractMessage');

    AbstractMessage.include({
        // Re-write to add synced attachments bkic
        getSyncedAttachments: function() {
            return _.filter(this.getAttachments(), function (attachment) {
                return attachment.cloud_key;
            });
        },
        getNotSyncedAttachments: function() {
            return _.difference(this.getAttachments(), this.getSyncedAttachments());
        },
        getImageAttachments: function () {
            return _.filter(this.getNotSyncedAttachments(), function (attachment) {
                return attachment.mimetype && attachment.mimetype.split('/')[0] === 'image';
            });            
        },
        getNonImageAttachments: function () {
            return _.difference(this.getNotSyncedAttachments(), this.getImageAttachments());
        },
        hasSyncedAttachments: function () {
            return this.getSyncedAttachments().length > 0;
        },
    });

});
