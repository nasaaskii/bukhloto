# -*- coding: utf-8 -*-

import pytz

from odoo import _, api, fields, models
from odoo.addons.mail.models.mail_template import format_tz
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import tools
from odoo.modules.module import get_module_resource

WRESTLER_STATE_SELECTION = [
        ('wrestling','Wrestling'), #Барилдаж байгаа
        ('retired','Retired'), #Зодог тайлсан
        ('damaged','Damaged'), #Гэмтсэн*Бэртсэн
    ]

class WrestlerRank(models.Model):
    _name = 'wrestler.rank'
    _description = 'Wrestler Rank'
    _inherit = ['mail.thread']
    _order="rate desc"
    
    RANK_SELECTION = [
        ('avarga','Avarga'),
        ('arslan','Arslan'),
        ('garid','Garid'),
        ('zaan','Zaan'),
        ('other','Other')
    ]    
        
    name = fields.Char(string='Name', required=True, size=64, track_visibility='always')
    rate = fields.Integer(string='Rate',track_visibility='always')
    static_rank = fields.Selection(RANK_SELECTION, string='Static rank', required=True, default='other', track_visibility='always')
    
    @api.constrains('rate')
    def _check_rate(self):
        if self.rate:
            self._cr.execute("select count(id) from wrestler_rank where rate = %s "
                       "and id <> %s",(self.rate, self.id))
            fetched = self._cr.fetchone()
            if fetched and fetched[0] and fetched[0] > 0:
                raise UserError(_('The Rate rank already exists !'))

class WrestlerGround(models.Model):
    '''ДЭВЖЭЭ БҮРТГЭЛ
    '''
    _name = 'wrestler.ground'
    _description = 'Wrestler ground'
    _inherit = ['mail.thread']
    
    name = fields.Char(string='Name', required=True, size=64)
    
    @api.constrains('name')
    def _check_name(self):
        if self.name:
            self._cr.execute("select count(id) from wrestler_ground where name = %s "
                       "and id <> %s",(self.name,self.id))
            fetched = self._cr.fetchone()
            if fetched and fetched[0] and fetched[0] > 0:
                raise UserError(_('The Ground already exists !'))

class WrestlerWrestler(models.Model):
    _name = 'wrestler.wrestler'
    _description = 'Wrestler'
    _inherit = ['mail.thread']
    _order = "rank_rate desc"
    
    STATE = [
        ('draft','Draft'),
        ('confirmed','Confirmed'),
    ]

    @api.multi
    def name_get(self):
        result = []
        for bukh in self:
            if bukh.is_template:
                name = u'%s'%(bukh.name)
                result.append((bukh.id, name))
            else:
                name = u'%s.%s - %s'%(bukh.name, bukh.last_name, bukh.rank_id.name)
                result.append((bukh.id, name))
        return result

    @api.multi
    @api.depends('name', 'last_name', 'rank_id', 'is_template')
    def _compute_name(self):
        if self.is_template:
            self.complete_name = u'%s'%(self.name)
        else:
            self.complete_name = u'%s.%s - %s'%(self.name, self.last_name, self.rank_id.name)
    
    @api.model
    def _default_image(self):
        image_path = get_module_resource('bukh_loto', 'static/img', 'default_image.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))
    
    image = fields.Binary("Photo", attachment=True,
        help="This field holds the image used as photo for the employee, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized photo", attachment=True,
        help="Medium-sized photo of the employee. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized photo", attachment=True,
        help="Small-sized photo of the employee. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    complete_name = fields.Char(string='Complete name',store=True, readonly=True, compute='_compute_name')
    name = fields.Char(string='Name', required=True, size=64,readonly=True, states={'draft': [('readonly', False)]})
    last_name = fields.Char(string='Last Name', required=True, size=64,readonly=True, states={'draft': [('readonly', False)]})
    ground_id = fields.Many2one('wrestler.ground', string='Ground', required=True, readonly=True, states={'draft': [('readonly', False)]})
    rank_id = fields.Many2one('wrestler.rank', string='Rank', required=True, readonly=True, states={'draft': [('readonly', False)]})
    rank_rate = fields.Integer(related='rank_id.rate', store=True, string='Rank Rate', readonly=True)
    static_rank = fields.Selection(related='rank_id.static_rank', store=True, string='Static rank', readonly=True)
    
    date_of_birth = fields.Date(string='Date Of Birth', readonly=True, states={'draft': [('readonly', False)]})
    place_of_birth = fields.Char(string='Place Of Birth', size=128,readonly=True, states={'draft': [('readonly', False)]})
    height = fields.Float(string='Height', digits=(16, 2),readonly=True, states={'draft': [('readonly', False)]})
    weight = fields.Float(string='Weight',digits=(16, 2),readonly=True, states={'draft': [('readonly', False)]})
    is_template = fields.Boolean(string='Is Template', default=False)
    
    #is_champian = fields.Boolean(string='Champian',readonly=True, states={'draft': [('readonly', False)]})
    #is_lion = fields.Boolean(string='Lion',readonly=True, states={'draft': [('readonly', False)]})
    #is_garuda = fields.Boolean(string='Garuda',readonly=True, states={'draft': [('readonly', False)]})static_rank
    #img_name = fields.Char(string='Image Name', required=True,size=128)
    status = fields.Selection(WRESTLER_STATE_SELECTION, string='Status', required=True, default='wrestling', track_visibility='always', readonly=True)
    state = fields.Selection(STATE, string='State', required=True, default='draft')
    
    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        return super(WrestlerWrestler, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(WrestlerWrestler, self).write(vals)
    
    @api.multi
    def action_open(self):
        return self.write({'state':'draft'})
    
    @api.multi
    def action_confirm(self):
        return self.write({'state':'confirmed'})
    
    @api.multi
    def action_back_injury(self):
        return self.write({'status':'wrestling'})
    
    @api.multi
    def action_juve(self):
        '''ЗОДОГ ТАЙЛАХ
        '''
        return self.write({'status':'retired'})

class WrestlerRank(models.Model):
    _inherit = 'wrestler.rank'
    wrestler_ids = fields.One2many('wrestler.wrestler', 'rank_id', string='Wrestler', readonly=True)

class WrestlerGround(models.Model):
    _inherit = 'wrestler.ground'
    wrestler_ids = fields.One2many('wrestler.wrestler', 'ground_id', string='Wrestler', readonly=True)

    