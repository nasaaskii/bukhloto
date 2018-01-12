# -*- coding: utf-8 -*-
import pytz
from odoo import _, api, fields, models
from odoo.addons.mail.models.mail_template import format_tz
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import tools
from odoo.tools.translate import html_translate
from dateutil.relativedelta import relativedelta

class EventWrestler(models.Model):
    _name = 'event.wrestler'
    _description = 'Event Wrestler'
    _inherit = ['mail.thread']

    wrestler_id = fields.Many2one('wrestler.wrestler', string='Wrestler', required=True)
    event_id = fields.Many2one('event.event', string='Event', required=True)
    
class EventEvent(models.Model):
    _inherit = 'event.event'

    wrestler_ids = fields.One2many('event.wrestler', 'event_id', string='Wrestler', readonly=True)
    wrestler_m2m_ids = fields.Many2many(comodel_name='wrestler.wrestler', string='Wrestlers')

    @api.multi
    def write(self, vals):
        res = super(EventEvent, self).write(vals)
        if vals.get('wrestler_m2m_ids'):
            wrestler_ids = vals.get('wrestler_m2m_ids')[0][2]
            self.env.cr.execute("delete from event_wrestler where event_id=%s"%(self.id))
            for wr in wrestler_ids:
                self.env['event.wrestler'].create({"event_id":self.id, "wrestler_id":wr})
        return res

class UserLoto(models.Model):
    _name = 'user.lotto'
    _description = 'User Lotto'
    _order = "point_index desc"

    @api.one
    @api.depends('step_1', 'step_2', 'step_3', 'step_4', 'step_5', 'step_6', 'step_7', 'step_8', 'step_9', 'step_10')
    def _compute_score(self):
        total_score = 0
        for obj in self:
            self.total_score = obj.step_1 + obj.step_2 + obj.step_3 + obj.step_4 + obj.step_5 + obj.step_6 + obj.step_7 + obj.step_8 + obj.step_9 + obj.step_10
        
    event_registration_id = fields.Many2one('event.registration', string='Event registration')
    point_index = fields.Integer(string='Point', default=1)
    wrestler_id = fields.Many2one('wrestler.wrestler', string='Wrestler', required=True)
    step_1 = fields.Integer(string='Step 1', default=0)
    step_2 = fields.Integer(string='Step 2', default=0)
    step_3 = fields.Integer(string='Step 3', default=0)
    step_4 = fields.Integer(string='Step 4', default=0)
    step_5 = fields.Integer(string='Step 5', default=0)
    step_6 = fields.Integer(string='Step 6', default=0)
    step_7 = fields.Integer(string='Step 7', default=0)
    step_8 = fields.Integer(string='Step 8', default=0)
    step_9 = fields.Integer(string='Step 9', default=0)
    step_10 = fields.Integer(string='Step 10', default=0)
    total_score = fields.Integer(string='Total Score',store=True, readonly=True, compute='_compute_score')

class EventRegistration(models.Model):
    _inherit = 'event.registration'
    _order = 'create_date desc'

    registerno = fields.Char(string='Register No', size=10)
    user_lotto_ids = fields.One2many('user.lotto', 'event_registration_id', string='User lotto', readonly=True, states={'draft': [('readonly', False)]})
    
    @api.model
    def _prepare_attendee_values(self, registration):
        """ Override to add sale related stuff """
        att_data = super(EventRegistration, self)._prepare_attendee_values(registration)
        registerno = registration.get('registerno')
        att_data.update({
            'registerno': registerno
        })
        return att_data
