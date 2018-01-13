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


class WrestlingResult(models.Model):
    '''Барилдааны үр дүн
    '''
    _name = 'wrestling.result'
    _description = 'Wrestling Result'
    _inherit = ['mail.thread']
    
    STATE_SELECTION = [
        ('draft','Draft'),
        ('confirmed','Confirmed'),
    ]
    
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
    
    name = fields.Char(string='Name', required=True, size=64, readonly=True, states={'draft': [('readonly', False)]})
    level = fields.Selection(LEVEL_SELECTION, string='Level', required=True, default='1', readonly=True, states={'draft': [('readonly', False)]})
    wrestling_id = fields.Many2one('event.event', string='Event', required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(STATE_SELECTION, string='Status', required=True, default='draft', readonly=True)
    date = fields.Date(string='Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
     
    is_finish_level = fields.Boolean(string='Is Finish Level')
    champion_wrestler_id = fields.Many2one('wrestler.wrestler', string='Champion Wrestler', readonly=True, states={'draft': [('readonly', False)]})
    is_rest_round_four = fields.Boolean(string='Is Rest Round Four?')
    is_rest_round_two = fields.Boolean(string='Is Rest Round Two?')
    
    @api.onchange('wrestling_id')
    def onchange_wrestling_id(self):
        wrestlers = []
        if self.wrestling_id:
            wrestlers = self.wrestling_id.wrestler_m2m_ids.ids
        return {'domain': {'champion_wrestler_id': [('id','in',wrestlers)]}}
    
    @api.constrains('wrestling_id','level')
    def _check_name(self):
        if self.wrestling_id and self.level:
            self._cr.execute("select count(id) from wrestling_result where wrestling_id = %s and level=%s "
                       "and id <> %s",(self.wrestling_id.id,self.level,self.id))
            fetched = self._cr.fetchone()
            if fetched and fetched[0] and fetched[0] > 0:
                raise UserError(_('The Result already exists !'))
            
    @api.multi
    def action_import_wrestler(self):
        if self.wrestling_id and self.wrestling_id.wrestler_m2m_ids: 
            for w in self.wrestling_id.wrestler_m2m_ids:
                not_lost = self.env['wrestling.result.history'].search([('wrestling_id','=',self.wrestling_id.id),('wrestler_id','=',w.id),('is_lost','=',False)])
                if not_lost:
                    line = self.env['wrestling.result.line'].create({'parent_id':self.id,
                                                                       'wrestler_id':w.id,
                                                                       'result_type':'won',
                                                                       'state':'draft',
                                                                       'wrestling_id':self.wrestling_id.id
                                                                       })
                
    @api.onchange('wrestling_id','level')
    def onchange_banzuuke(self):
        if self.wrestling_id and self.level:
            self.update({'name':u'%s, Даваа: %s'%(self.wrestling_id.name, self.level)})
    
#      ('avarga','Avarga'),
#         ('arslan','Arslan'),
#         ('garid','Garid'),
#         ('zaan','Zaan'),
#         ('other','Other')
        
    @api.multi
    def compute_point(self, line, history, is_won):
        point = 0
        if is_won:
            if line.rival_wrestler_rank_id.static_rank == 'avarga':
                point += 20
            if line.rival_wrestler_rank_id.static_rank == 'arslan':
                point += 15
            if line.rival_wrestler_rank_id.static_rank == 'garid':
                point += 10
            if line.rival_wrestler_rank_id.static_rank == 'zaan':
                point += 5
        else:
            point = 0
        return point
    
    @api.multi
    def write_user_loto(self, line, point, event_registration_ids):
        user_lotos = self.env['user.lotto'].search([('event_registration_id','in',event_registration_ids),
                                                        ('wrestler_id','=',line.wrestler_id.id)
                                                        ])
        if user_lotos:
            for loto in user_lotos:
                index_point = point
                if self.is_rest_round_four:
                    index_point += 10
                
                if self.is_rest_round_two:
                    index_point += 20
                    
                if line.result_type == 'won':
                    index_point += loto.point_index
                    
                    if self.is_finish_level:
                        if self.champion_wrestler_id:
                            is_champion=False
                            if line.wrestler_id.id == self.champion_wrestler_id.id:
                                index_point += 30
                                is_champion=True
                            
                if self.level == '1':
                    loto.write({'step_1':index_point})
                if self.level == '2':
                    loto.write({'step_2':index_point})
                if self.level == '3':
                    loto.write({'step_3':index_point})
                if self.level == '4':
                    loto.write({'step_4':index_point})
                if self.level == '5':
                    if line.result_type == 'won':
                         index_point += 5
                    loto.write({'step_5':index_point})
                if self.level == '6':
                    if line.result_type == 'won':
                        index_point += 5
                    loto.write({'step_6':index_point})
                if self.level == '7':
                    if line.result_type == 'won':
                        index_point += 5
                    loto.write({'step_7':index_point})
                if self.level == '8':
                    if line.result_type == 'won':
                        index_point += 5
                    loto.write({'step_8':index_point})
                if self.level == '9':
                    if line.result_type == 'won':
                        index_point += 5
                    loto.write({'step_9':index_point})
                if self.level == '10':
                    if line.result_type == 'won':
                        index_point += 5
                    loto.write({'step_10':index_point})
        return {}
    
    @api.multi
    def action_confirm(self):
        history_obj = self.env['wrestling.result.history']
        history_line_obj = self.env['wrestling.result.history.line']
        for line in self.line_ids:
            won_history = history_obj.search([('wrestler_id','=',line.wrestler_id.id),('wrestling_id','=',self.wrestling_id.id)])
            if not won_history:
                raise UserError((u'%s, %s барилдааны үр дүн олдсонгүй!'%(line.wrestler_id.name, self.wrestling_id.name)))
            
            if self.champion_wrestler_id:
                if self.champion_wrestler_id.id == line.wrestler_id.id:
                    won_history.write({'is_champion':True})
            
            if self.is_rest_round_four:
                won_history.write({'is_rest_round_four':True})
                
            if self.is_rest_round_two:
                won_history.write({'is_rest_round_two':True})
                
            event_registration_ids=[]
            event_registrations = self.env['event.registration'].search([('event_id', '=', self.wrestling_id.id), ('state','=','open')])
            if event_registrations:
                event_registration_ids = event_registrations.ids
            
            if not event_registration_ids:
                raise UserError((u'Оролцогч хоосон байна!'))
            
            if won_history:
                if line.result_type == 'won':
                    point = self.compute_point(line,won_history,True)
                    self.write_user_loto(line, point, event_registration_ids)
                    history_line_obj.create({'parent_id':won_history.id,
                                             'level':self.level,
                                             'result_type':'won',
                                             'rival_wrestler_id':line.rival_wrestler,
                                             'rival_wrestler_rank_id':line.rival_wrestler_rank_id.id,
                                             'tehnic':line.tehnic,
                                             'origin_id':line.id,
                                             'point':point
                                             })
                else:
                    won_history.write({'is_lost':True})
                    point = self.compute_point(line,won_history,False)
                    self.write_user_loto(line, point, event_registration_ids)
                    history_line_obj.create({'parent_id':won_history.id,
                                             'level':self.level,
                                             'result_type':'lost',
                                             'rival_wrestler_id':line.rival_wrestler,
                                             'rival_wrestler_rank_id':line.rival_wrestler_rank_id.id,
                                             'tehnic':line.tehnic,
                                             'origin_id':line.id,
                                             'point':point,
                                             })
        self.line_ids.write({'state':'confirmed'})
        return self.write({'state':'confirmed'})
    
class WrestlingResultLine(models.Model):
    _name = 'wrestling.result.line'
    _description = 'Wrestling Result line'
    
    STATE_SELECTION = [
        ('draft','Draft'),
        ('confirmed','Confirmed'),
    ]
    
    parent_id = fields.Many2one('wrestling.result', string='Parent', ondelete='cascade')
    wrestling_id = fields.Many2one('event.event', string='Event')
    wrestler_id = fields.Many2one('wrestler.wrestler', 'Wrestler', required=True)
    wrestler_rank_id = fields.Many2one(related='wrestler_id.rank_id', store=True, string='Wrestler Rank', readonly=True)
    result_type = fields.Selection([('won','Won'),
                                    ('lost','Lost'),
                                    ('missed','Missed'),
                                    ], string='Result Type', required=True)
    tehnic = fields.Char(string='Tehnic', size=128)
    rival_wrestler = fields.Char(string='Rival Wrestler', size=128)
    rival_wrestler_rank_id = fields.Many2one('wrestler.rank', string='Rival Wrestler Rank')
    state = fields.Selection(STATE_SELECTION, string='Status', required=True, default='draft')

    @api.constrains('wrestler_id')
    def _check_name(self):
        if self.wrestler_id and self.parent_id:
            self._cr.execute("select count(id) from wrestling_result_line where wrestler_id=%s and parent_id=%s "
                       "and id <> %s",(self.wrestler_id.id,self.parent_id.id,self.id))
            fetched = self._cr.fetchone()
            if fetched and fetched[0] and fetched[0] > 0:
                raise UserError(_('The Wrestler already exists ! [%s]'%(self.wrestler_id.name)))
    @api.multi
    def unlink(self):
        for loto in self:
            if loto.state != 'draft':
                raise UserError(_('You can only delete draft record!'))
        return super(WrestlingResultLine, self).unlink()
    
    @api.onchange('wrestling_id')
    def onchange_wrestling_id(self):
        wrestlers = []
        if self.wrestling_id:
            wrestlers = self.wrestling_id.wrestler_m2m_ids.ids
        return {'domain':{'wrestler_id':[('id','in',wrestlers)]}}
    
class WrestlingResult(models.Model):
    _inherit = 'wrestling.result'
    line_ids = fields.One2many('wrestling.result.line', 'parent_id', string='Lines',readonly=True, states={'draft': [('readonly', False)]})
    
    @api.multi
    def unlink(self):
        for loto in self:
            if loto.state != 'draft':
                raise UserError(_('You can only delete draft record!'))
        return super(WrestlingResult, self).unlink()
    
    