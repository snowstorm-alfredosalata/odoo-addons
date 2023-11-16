# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class sync_log(models.Model):
    """
    The model to keep logs of syncing with cloud client
    """
    _name = "sync.log"
    _description = "Sync Log"

    name = fields.Text(string="Message")
    ttype = fields.Selection(
        [            
            ("success", "Success"),
            ("warning", "Warning"),
            ("failure", "Failure"),
        ],
        string="Type",
    )
    log_time = fields.Datetime(string="Log Time",)

    _order = "log_time DESC, id DESC"

    @api.model
    def warning(self, log_message):
        """
        The method to post logger and create sync.log if defined
        """
        _logger.warning(log_message)
        self.create({
            "name": log_message,
            "ttype": "warning",
            "log_time": fields.Datetime.now(),
        })

    @api.model
    def error(self, log_message):
        """
        The method to post logger and create sync.log if defined
        """
        _logger.error(log_message)
        self.create({
            "name": log_message,
            "ttype": "failure",
            "log_time": fields.Datetime.now(),
        })

    @api.model
    def info(self, log_message):
        """
        The method to post logger and create sync.log if defined
        """
        _logger.info(log_message)
        self.create({
            "name": log_message,
            "ttype": "success",
            "log_time": fields.Datetime.now(),
        })

    @api.model
    def debug(self, log_message):
        """
        The method to post logger and create sync.log if defined
        """
        _logger.debug(log_message)
        self.create({
            "name": log_message,
            "ttype": "success",
            "log_time": fields.Datetime.now(),
        })
