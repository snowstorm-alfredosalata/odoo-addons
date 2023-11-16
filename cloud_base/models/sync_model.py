# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

FORBIDDENMODELS = [
    "ir.module.module", "mail.activity.mixin", "mail.thread",
]


class sync_model(models.Model):
    """
    The model to manage model (+domain) - cloud folder relation
    """
    _name = "sync.model"
    _description = "List of Odoo Synced Models"

    @api.depends("period_ids", "period_ids.field_id", "period_ids.period_value",
                 "period_ids.period_type", "period_ids.inclusive_this")
    def _compute_period_title(self):
        """
        Compute method for period_title & period_domain

        Methods:
         * _return_period_domain_and_title
        """
        for sync_model in self:
            period_domain, period_title = sync_model._return_period_domain_and_title()
            sync_model.period_domain = period_domain
            sync_model.period_title = period_title

    @api.depends("last_sync_datetime")
    def _compute_nosyncd(self):
        """
        Compute method for nosyncd
        """
        for folder in self:
            nosyncd = False
            if folder.last_sync_datetime:
                nosyncd = True
            folder.nosyncd = nosyncd

    def _inverse_name(self):
        """
        Inverse method for name:
         * to make name safe (without illegal charachers)
         * to make it unique

        Methods:
         * remove_illegal_characters of ir.attachment
        """
        for on_model in self:
            legal_name = self.env["ir.attachment"].remove_illegal_characters(on_model.name)
            if not legal_name:
                legal_name = str(on_model.id)
            with_the_same_name = self.search([("name", "=", legal_name), ("id", "!=", on_model.id)])
            itera = 1
            name_core = legal_name
            while with_the_same_name:
                legal_name = u"{} ({})".format(name_core, itera)
                itera += 1
                with_the_same_name = self.search([("name", "=", legal_name), ("id", "!=", on_model.id)])
            if self.name != legal_name:
                self.name = legal_name

    @api.onchange("model_id")
    def _onchange_model_id(self):
        """
        Onchange method for model_id

        Attrs update:
         * name
        """
        for on_model in self:
            if on_model.model_id:
                if on_model.model_id.model == "ir.attachment":
                    on_model.name = _("Stand alone attachments")
                else:
                    on_model.name = self.model_id.name
            on_model.domain = "[]"
            on_model.default_folders = "[]"
            on_model.period_ids = False

    name = fields.Char(
        string="Folder name",
        inverse=_inverse_name,
    )
    synced_name = fields.Char(
        string="Synced name",
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model to sync",
        domain=[
            ("model", "not in", FORBIDDENMODELS),
            ("transient", "=", False),
        ],
        ondelete='cascade',
    )
    model = fields.Char(
        related="model_id.model",
        store=True,
    )
    domain = fields.Text(
        string="Filtering",
        default="[]",
    )
    period_ids = fields.One2many(
        "cloud.domain.period",
        "sync_model_id",
        string="Periods",
    )
    period_domain  = fields.Char(
        string="Domain by periods",
        compute=_compute_period_title,
    )
    period_title = fields.Char(
        string="If today, the periods would be",
        compute=_compute_period_title,
    )
    key = fields.Char(string="ID in client")
    path = fields.Char(string="Path")
    sync_object_ids = fields.One2many(
        "sync.object",
        "sync_model_id",
        string="Objects Folders",
    )
    last_sync_datetime = fields.Datetime(string="Direct Sync Time")
    last_backward_sync_datetime = fields.Datetime(string="Direct Backward Sync Time")
    nosyncd = fields.Boolean(
        string="Not synced",
        compute=_compute_nosyncd,
        store=True,
    )
    sequence = fields.Integer(string="Sequence")
    default_folders = fields.Char(
        string="Default Folders",
        default="[]"
    )
    name_expression = fields.Text("Name Expression")

    _order = "sequence, id"

    def _make_cloud_models(self, root_key, root_path):
        """
        Methods to prepare model folders in cloud
         1. Firstly we try to check deleted but needed folders
          1.1 Key of such folders are not any more valid --> clean them
         2. For the sudden case some model was removed
         3. Create not yet synced models folders in cloud
         4. Update existing cloud folder, in case name is changed since the last sync
          4.1. If path was updated in client we should write it immediately

        Args:
         * root_id - parent directory client id
         * root_path - parent directory name

        Methods:
         * _return_child_items of ir.attachment
         * _send_model_folder
         * _check_model_folder
         * _update_model_folder

        Extra info:
         * We do not check that this model exists, since we have done it in batch in parent method

        Returns:
         * None - if error; True otherwise
        """
        # 1
        client_items = self.env["ir.attachment"]._return_child_items(folder_id=False, key=root_key, path=root_path)
        if client_items is None:
            return None
        client_items_set = {i['id'] for i in client_items}
        odoo_items = self.mapped("key")
        odoo_items_set = set(odoo_items)
        to_recover_models_set = odoo_items_set - client_items_set
        to_recover_models = self.filtered(lambda mod: mod.key in to_recover_models_set)
        # 1.1
        to_recover_models.write({"key": False})
        for model in self:
            if not model.model_id or not model.name:
                # 2
                _logger.critical(u"Synced folder with ID {}, name - {} doesn't have name or model linked".format(
                    model.id, model.name
                ))
            elif not model.key:
                # 3
                model._send_model_folder(root_key=root_key, root_path=root_path)
                self._cr.commit()
            else:
                # 4
                client_data = [[item["name"], item["path"]] for item in client_items if item["id"] == model.key][0]
                cfolder_name, cfolder_path = client_data[0], client_data[1]
                # 4.1
                if model.path != cfolder_path:
                    model.path = cfolder_path
                new_synced_name = model.name
                if new_synced_name != cfolder_name:
                    model._update_model_folder(new_synced_name=new_synced_name)
                    self._cr.commit()
            today_now = fields.Datetime.now()
            model.write({"last_sync_datetime": today_now,})
            self._cr.commit()
        return True

    def _send_model_folder(self, root_key, root_path):
        """
        The method to generate a new model folder in cloud

        Methods:
         * _create_folder of ir.attachment
         * write
        """
        ir_attachment = self.env["ir.attachment"]
        for sync_model in self:
            sync_model_name = sync_model.name
            key, path = ir_attachment._create_folder(
                folder_name=sync_model_name,
                parent_folder_key=root_key,
                parent_folder_path=root_path,
            )
            if key and path:
                sync_model.write({
                    "key": key,
                    "path": path,
                    "synced_name": sync_model_name,
                })

    def _update_model_folder(self, new_synced_name):
        """
        The method to update folder name in cloud

        Args:
         * new_synced_name - char - new name

        Methods:
         * _update_folder of ir.attachment
         * write
        """
        ir_attachment = self.env["ir.attachment"]
        for sync_model in self:
            key, path = ir_attachment._update_folder(
                folder_id=self,
                new_folder_name=new_synced_name,
            )
            if key and path:
                sync_model.write({
                    "key": key,
                    "path": path,
                    "synced_name": new_synced_name,
                })

    def _return_children(self):
        """
        The method to return all child elements of this folder in Client

        Methods:
         * _return_child_items of ir.attachment

        Returns:
         * list of of child dicts including name, id, webUrl, path
         * None if error

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        ir_attachment = self.env["ir.attachment"]
        child_ids = ir_attachment._return_child_items(folder_id=self)
        return child_ids

    def _return_children_batch(self):
        """
        The method to return all child elements of a few model folders

        Methods:
         * _return_children

        Returns:
         * list of of child dicts including name, id, webUrl, path
         * None if error
        """
        batch_child_ids = []
        for sync_model in self:
            child_ids = sync_model._return_children()
            if child_ids is None:
                return None
            if child_ids:
                batch_child_ids += child_ids
        return batch_child_ids

    def _return_sync_domain(self):
        """
        The method to return sync domain

        Methods:
         * _return_period_domain_and_title()

        Returns:
         * list - RPR

        Extra info:
         * We do not use the computed fields to avoid concurrent update
         * Expected singleton
        """
        self.ensure_one()
        period_domain, period_title = self._return_period_domain_and_title()
        result_domain = safe_eval(self.domain) + period_domain
        return result_domain

    def _return_period_domain_and_title(self):
        """
        The method to construct period domain and title

        Returns:
         * list - RPR
         * char

        Methods:
         * _return_translation_for_field_label

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        merged_periods = {}
        for period in self.period_ids:
            field = self._return_translation_for_field_label(field=period.field_id)
            if merged_periods.get(field):
                or_str = _("or")
                merged_periods[field] = {
                    "domain": ['|'] + merged_periods[field]["domain"] + safe_eval(period.domain),
                    "title": u"{} {} {}".format(merged_periods[field]["title"], or_str,  period.title)
                }
            else:
                merged_periods[field] = {
                    "domain": safe_eval(period.domain),
                    "title": period.title,
                }
        domain = []
        title = ""
        for field, values in merged_periods.items():
            domain += values["domain"]
            title += "{}: {}; ".format(field, values["title"])
        return domain, title

    def _return_translation_for_field_label(self, field):
        """
        The method to return translation for field label

        Args:
         * ir.model.fields object

        Returns:
         * char

        Extra info:
         * Expected singleton or empty recordset
        """
        lang = self._context.get("lang") or self.env.user.lang
        return  field.with_context(lang=lang).field_description
