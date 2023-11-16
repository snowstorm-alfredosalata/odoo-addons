# -*- coding: utf-8 -*-

import base64
import io
import zipfile

from odoo.http import request, content_disposition

from odoo.addons.documents.controllers.main import ShareRoute


FORBIDDEN_MIMETYPES = ["application/octet-stream", "special_cloud_folder"]


class ShareRouteClass(ShareRoute):
    """
    Re-write to make possible donwload of cloud files instead of opening an url
    """

    def _make_zip(self, name, documents):
        """
        Fully re-write since we need to process cloud files to zip as well
        """
        stream = io.BytesIO()
        try:
            with zipfile.ZipFile(stream, 'w') as doc_zip:
                for document in documents:
                    if document.type not in ['binary', 'url']:
                        continue
                    if document.type == "url":
                        if document.attachment_id.cloud_key and \
                                document.attachment_id.mimetype not in FORBIDDEN_MIMETYPES:
                            content_base64 = document.attachment_id.datas
                            if not content_base64:
                                continue
                            content = base64.b64decode(content_base64)
                            filename = document.attachment_id.name
                        else:
                            continue
                    else:
                        status, content, filename, mimetype, filehash = request.env['ir.http']._binary_record_content(
                            document, field='datas', filename=None, filename_field='name',
                            default_mimetype='application/octet-stream')
                    doc_zip.writestr(filename, base64.b64decode(content),
                                     compress_type=zipfile.ZIP_DEFLATED)
        except zipfile.BadZipfile:
            logger.exception("BadZipfile exception")

        content = stream.getvalue()
        headers = [
            ('Content-Type', 'zip'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(name))
        ]
        return request.make_response(content, headers)
