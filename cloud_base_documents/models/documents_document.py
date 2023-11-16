# -*- coding: utf-8 -*-

from odoo import api, fields, models


class documents_document(models.Model):
    """
    Overwritting to make sync of Odoo document folders and their attachments
    """
    _inherit = "documents.document"

    @api.depends('attachment_type', 'url', 'attachment_id.type')
    def _compute_type(self):
        """
        Re-write to make possible url base on attachment url
        """
        for record in self:
            record.type = 'empty'
            if record.attachment_id:
                record.type = record.attachment_id.type in ["binary", "url"] and record.attachment_id.type or 'binary'
            elif record.url:
                record.type = 'url'

    @api.depends('checksum')
    def _compute_thumbnail(self):
        """
        Re-write to avoid upload file consistent error
        """
        for record in self:
            if record.cloud_key:
                record.thumbnail = False
            else:
                super(documents_document, self)._compute_thumbnail()


    type = fields.Selection(compute=_compute_type)
    cloud_key = fields.Char(
        related="attachment_id.cloud_key",
        compute_sudo=True,
    )

    def _get_changes_from_attachments(self):
        """
        The method to reflect changes from updated attachments
        """
        for document in self:
            attachment_id = document.attachment_id
            document.write({
                "attachment_id": attachment_id.id, # to trigger related
                "url": attachment_id.url,
            })
        self.env.cr.commit()

    def action_donwload_cloud_file(self):
        """
        The method to retrieve content from clouds
        
        Methods:
         * upload_attachment_from_cloud_ui of ir.attachment

        Returns:
         * action dict

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        return self.attachment_id.upload_attachment_from_cloud_ui()
