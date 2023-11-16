odoo.define('cloud_base.chatter', function (require) {
"use strict";
    
    var core = require('web.core');
    var Chatter = require('mail.Chatter');
    var _t = core._t;
    var rpc = require('web.rpc');


    Chatter.include({
        init: function (parent, record, mailFields, options) {
            this._super.apply(this, arguments);
            this.cloudSynced = false;
        },
        start: function () {
            // Re-write to calculate whether this document is synced
            var self = this;
            rpc.query({
                model: "sync.object",
                method: 'is_this_document_synced',
                args: [self.record.model, self.record.res_id],
            }).then(function (res) {
                self.cloudSynced = res;
            }); 
            return this._super.apply(this, arguments);    
        },
    });

    return Chatter

});
