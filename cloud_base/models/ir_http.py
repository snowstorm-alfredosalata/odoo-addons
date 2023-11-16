# -*- coding: utf-8 -*-


from odoo import models, registry
from odoo.http import request


class IrHttp(models.AbstractModel):
    """
    Re-write to add processing attachment from clouds
    """
    _inherit = 'ir.http'
    
    @classmethod
    def _binary_ir_attachment_redirect_content(cls, record, default_mimetype='application/octet-stream'):
        """
        Re-write to make routes work (mainly for 'sign' and preview)        
        """
        status, content, filename, mimetype, filehash = super(IrHttp, cls)._binary_ir_attachment_redirect_content(
            record=record, default_mimetype=default_mimetype
        )
        if record.cloud_key and record.type == 'url' and record.url:
            try:
                content = record.datas or ""
                filename = record.name
                status = content and 200 or 301
            except:
                content = record.url
                status = 301
        return status, content, filename, mimetype, filehash