# -*- coding: utf-8 -*-

import base64
import werkzeug

from odoo.http import route, request, content_disposition

from odoo.addons.web.controllers.main import Binary


class BinaryClass(Binary):

    @route('/web/cloud_content/<int:id>', type='http', auth='public')
    def request_cloud_datas(self, id, **kwargs):
        """
        The controller to donwload received from cloud binary
        """
        try:
            attachment = request.env["ir.attachment"].browse(id)
            content = attachment.datas
            content_base64 = base64.b64decode(content)
            headers = [
                ('Content-Type', attachment.mimetype), 
                ('X-Content-Type-Options', 'nosniff'),
                ('Content-Length', len(content_base64)),
                ('Cache-Control', 'max-age=0'),
                ('Content-Disposition', content_disposition(attachment.name)),
            ]
            response = request.make_response(content_base64, headers)
        except:
            response = request.not_found()
        return response     
