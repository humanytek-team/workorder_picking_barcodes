# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from openerp import api
from openerp.exceptions import UserError, RedirectWarning, ValidationError

from odoo.tools import float_compare, float_round
from odoo.addons import decimal_precision as dp
 

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'


    @api.multi
    def show_pickings(self):
        for workorder in self:
            order = workorder.production_id
            if order:
                res = []
                picking_ids = self.env['stock.picking'].search([('origin','=',order.name)])
                res = [x.id for x in picking_ids]
                print 'res: ',res
                print "[('id','in',[" + ','.join(map(str, list(res))) + "])]"
                if not res:
                    raise UserError(_('Warning !\nThere are no pikings for this Manufacturing Order'))
                return {
                        'domain': "[('id','in',[" + ','.join(map(str, list(res))) + "])]",
                        'name'      : _('Pickings'),
                        'view_mode': 'tree,form',
                        'view_type': 'form',
                        #'context': {'tree_view_ref': 'stock.view_picking_form'},
                        'res_model': 'stock.picking',
                        'type': 'ir.actions.act_window',
                    }

    @api.multi
    def _compute_post_visible(self):
        """
        CHECKS PRODUCTION TO SEE IF POST_VISIBLE IS TRUE
        """
        for workorder in self:
            order = workorder.production_id
            if order:
                workorder.post_visible = order.post_visible


    post_visible = fields.Boolean(
        'Inventory Post Visible', compute='_compute_post_visible',
        help='Technical field to check when we can post')


    @api.multi
    def workorder_post_inventory(self):
        for workorder in self:
            order = workorder.production_id
            if order:
                moves_not_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done')
                moves_to_do = order.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                moves_to_do.action_done()
                moves_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done') - moves_not_to_do
                order._cal_price(moves_to_do)
                moves_to_finish = order.move_finished_ids.filtered(lambda x: x.state not in ('done','cancel'))
                moves_to_finish.action_done()
                
                for move in moves_to_finish:
                    #Group quants by lots
                    lot_quants = {}
                    raw_lot_quants = {}
                    quants = self.env['stock.quant']
                    if move.has_tracking != 'none':
                        for quant in move.quant_ids:
                            lot_quants.setdefault(quant.lot_id.id, self.env['stock.quant'])
                            raw_lot_quants.setdefault(quant.lot_id.id, self.env['stock.quant'])
                            lot_quants[quant.lot_id.id] |= quant
                    for move_raw in moves_to_do:
                        if (move.has_tracking != 'none') and (move_raw.has_tracking != 'none'):
                            for lot in lot_quants:
                                lots = move_raw.move_lot_ids.filtered(lambda x: x.lot_produced_id.id == lot).mapped('lot_id')
                                raw_lot_quants[lot] |= move_raw.quant_ids.filtered(lambda x: (x.lot_id in lots) and (x.qty > 0.0))
                        else:
                            quants |= move_raw.quant_ids.filtered(lambda x: x.qty > 0.0)
                    if move.has_tracking != 'none':
                        for lot in lot_quants:
                            lot_quants[lot].sudo().write({'consumed_quant_ids': [(6, 0, [x.id for x in raw_lot_quants[lot] | quants])]})
                    else:
                        move.quant_ids.sudo().write({'consumed_quant_ids': [(6, 0, [x.id for x in quants])]})
                order.action_assign()
        return True
