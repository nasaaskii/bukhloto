# -*- coding: utf-8 -*-

import pytz

from odoo import _, api, fields, models
from odoo.addons.mail.models.mail_template import format_tz
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import tools
from odoo.modules.module import get_module_resource

class WrestlingResultHistory(models.Model):
    _name = 'wrestling.result.history'
    _description = 'Wrestling Result History'
    _order="wrestling_id"
    
    @api.one
    @api.depends('line_ids')
    def _compute_win(self):
        win = 0
        for line in self.line_ids:
            if line.result_type == 'won':
                win += 1
        self.win_count = win
        
    wrestling_id = fields.Many2one('event.event',string='Wrestling', required=True, readonly=True)
    wrestler_id = fields.Many2one('wrestler.wrestler', string='Wrestler', required=True, readonly=True)
    
    win_count = fields.Integer(compute='_compute_win', string='Win Count', readonly=True,store=True)
    is_champion = fields.Boolean(string='Is Champion', readonly=True)
    is_lost = fields.Boolean(string=u'Унасан эсэх', readonly=True, default=False)
    is_rest_round_four = fields.Boolean(string='Is Rest Round Four', readonly=True)
    is_rest_round_two = fields.Boolean(string='Is Rest Round Two', readonly=True)
    
    @api.constrains('wrestling_id','wrestler_id')
    def _check_name(self):
        if self.wrestling_id and self.wrestler_id:
            self._cr.execute("select count(id) from wrestling_result_history where wrestling_id=%s and wrestler_id=%s "
                       "and id <> %s",(self.wrestling_id.id,self.wrestler_id.id,self.id))
            fetched = self._cr.fetchone()
            if fetched and fetched[0] and fetched[0] > 0:
                raise UserError(_('The Result history already exisits ! [%s, %s]'%(self.wrestling_id.name, self.wrestler_id.name)))
            
class WrestlingResultHistoryLine(models.Model):
    _name = 'wrestling.result.history.line'
    _description = 'Wrestling Result History Line'
    _order="level"
    
    LEVEL_SELECTION = [
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5'),
        ('6','6'),
        ('7','7'),
        ('8','8'),
        ('9','9'),
        ('10','10'),
    ]
        
    parent_id = fields.Many2one('wrestling.result.history',string='Parent')
    level = fields.Selection(LEVEL_SELECTION, string='Level', required=True, default='1', readonly=True)
    result_type = fields.Selection([('won','Won'),
                                    ('lost','Lost'),
                                    ('missed','Missed'),
                                    ], string='Result Type', required=True, readonly=True)
    rival_wrestler_id = fields.Char(string='Rival Wrestler', readonly=True, size=128)
    rival_wrestler_rank_id = fields.Many2one('wrestler.rank', string='Rank', readonly=True)
    tehnic = fields.Char(string='Tehnic',size=128,readonly=True)
    point = fields.Integer(string='Point', readonly=True)
    origin_id = fields.Many2one('wrestling.result.line', string='Origin', readonly=True)
    
class WrestlingResultHistory(models.Model):
    _inherit = 'wrestling.result.history'
    line_ids = fields.One2many('wrestling.result.history.line', 'parent_id', string='Parent', readonly=True)
    
class WrestlerWrestler(models.Model):
    _inherit = 'wrestler.wrestler'

    wrestling_ids = fields.One2many('wrestling.result.history', 'wrestler_id', string='Wrestling', readonly=True)


