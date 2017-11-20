# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, RedirectWarning, ValidationError

# class StockPicking(models.Model):
#     _inherit = ['stock.picking']

#     @api.multi
#     def get_mo(self):
#         print 'get_mo'
#         mrp = self.env['mrp.production']
#         for picking in self:
#             if picking.origin:
#                 res = mrp.search([('name','=',picking.origin),('state','!=',"cancel")])
#                 print 'res: ',res
#                 if res:
#                     return res[0]
#         return False


class MrpWorkorder(models.Model):
    _inherit = ['mrp.workorder']

    @api.multi
    def get_picking(self):
        print 'get_picking'
        obj = self.env['stock.picking']
        for workorder in self:
            if workorder.production_id:
                domain = ('cancel','done')
                res = obj.search([('origin','=',workorder.production_id.name),('state','not in',domain)])
                print 'res: ',res
                if res:
                    print 'res[0].id: ',res[0].id
                    print 'res[0].name: ',res[0].name
                    return res[0]
        return False





