# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import babel.dates
import re
import werkzeug
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import fields, http, _
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug

class WebsiteEventSaleController(WebsiteEventController):

    @http.route(['/event/<model("event.event"):event>/register'], type='http', auth="public", website=True)
    def event_register(self, event, **post):
        event = event.with_context(pricelist=request.website.get_current_pricelist().id)
        return super(WebsiteEventSaleController, self).event_register(event, **post)

    def _process_tickets_details(self, data):
        ticket_post = {}
        for key, value in data.items():
            if not key.startswith('nb_register') or '-' not in key:
                continue
            items = key.split('-')
            if len(items) < 2:
                continue
            ticket_post[int(items[1])] = int(value)
        tickets = request.env['event.event.ticket'].browse(tuple(ticket_post))
        return [{'id': ticket.id, 'name': ticket.name, 'quantity': ticket_post[ticket.id], 'price': ticket.price} for ticket in tickets if ticket_post[ticket.id]]
    
    @http.route(['/event/<model("event.event"):event>/registration/new'], type='json', auth="public", methods=['POST'], website=True)
    def registration_new(self, event, **post):
        tickets = self._process_tickets_details(post)
        if not tickets:
            return False
        return request.env['ir.ui.view'].render_template("website_event.registration_attendee_details", {'tickets': tickets, 'event': event})
    
class WebsiteEventController(http.Controller):
    
    def _process_registration_details(self, details):
        ''' Process data posted from the attendee details form. '''
        registrations = {}
        global_values = {}
        for key, value in details.items():
            counter, field_name = key.split('-', 1)
            if counter == '0':
                global_values[field_name] = value
            else:
                registrations.setdefault(counter, dict())[field_name] = value
        for key, value in global_values.items():
            for registration in registrations.values():
                registration[key] = value
        return list(registrations.values())
    
    @http.route(['/event/<model("event.event"):event>/registration/confirm'], type='http', auth="public", methods=['POST'], website=True)
    def registration_confirm(self, event, **post):
        Attendees = request.env['event.registration']
        UserLotto = request.env['user.lotto']
        registrations = self._process_registration_details(post)
        event_registration_obj=False
        user_lotto_obj = False
        wrestler_vals = []
        for registration in registrations:
            if registration.get('name') and registration.get('phone'):
                registration['event_id'] = event
                Attendees += Attendees.sudo().create(
                    Attendees._prepare_attendee_values(registration))
                event_registration_obj = Attendees
            wrestler_vals.append({'point_index':'1', 'wrestler_id':int(registration.get('1'))})
            wrestler_vals.append({'point_index':'2', 'wrestler_id':int(registration.get('2'))})
            wrestler_vals.append({'point_index':'3', 'wrestler_id':int(registration.get('3'))})
            wrestler_vals.append({'point_index':'4', 'wrestler_id':int(registration.get('4'))})
            wrestler_vals.append({'point_index':'5', 'wrestler_id':int(registration.get('5'))})
            wrestler_vals.append({'point_index':'6', 'wrestler_id':int(registration.get('6'))})
            wrestler_vals.append({'point_index':'7', 'wrestler_id':int(registration.get('7'))})
            wrestler_vals.append({'point_index':'8', 'wrestler_id':int(registration.get('8'))})

        if wrestler_vals:
            for wval in wrestler_vals:
                UserLotto += UserLotto.sudo().create(wval)
                
        if event_registration_obj and UserLotto:
            UserLotto.sudo().write({'event_registration_id':event_registration_obj.id})
        return request.render("website_event.registration_complete", {
            'attendees': Attendees,
            'event': event,
        })

class WebsiteCheckLotto(http.Controller):
    
    @http.route([
        '/checklotto',
        '/checklotto/lotto/<model("event.registration"):registration>'
    ], type='http', auth="public", website=True)
    def checklotto(self, page=0, search='', **post):
        lotto = False
        user_lotto = request.env['event.registration']
        lottos = user_lotto.search([('phone','=', search)])
        if not lottos:
            lottos = user_lotto.search([('registerno','=', search)])
        return request.render("bukh_loto.website_check_lotto", {'lottos':lottos})
    