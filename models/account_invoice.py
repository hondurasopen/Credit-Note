# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare

class Notascredito(models.Model):
    _inherit = "account.invoice"

    @api.one
    def _compute_get_note(self):
        if self.type == 'out_invoice':
            inv_obj_refund = self.env["account.invoice"].search([('type', '=', 'out_refund'), ('origin', '=', self.number)])
            if inv_obj_refund:
                for refund in inv_obj_refund:
                    if refund.state == 'open' or refund.state == 'paid':
                        self.amount_credit_note += refund.amount_total

    @api.one
    def _compute_check(self):
        if self.state == 'open' and self.type == 'out_invoice':
            if self.residual == 0:
                query = """ UPDATE account_invoice  SET state='paid' WHERE id = %s """
                self._cr.execute(query, (self.id,))
                self.check_status = True

    amount_credit_note = fields.Float("Credit note amount", domain=[('type', '=', 'out_invoice')], compute='_compute_get_note')
    check_status = fields.Boolean("Invoice paid", compute='_compute_check')
    nota_debito = fields.Boolean("Nota de Debito")

    @api.multi
    def get_action_credit_note(self):
        view_id = self.env.ref("credit.note.credit_note_view_invoice", False)
        for inv in self:
            return {
                'name': ("Credi Note Customer"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'credit.note',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
            }

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self.sudo().move_id.line_ids:
            if line.account_id.internal_type in ('receivable', 'payable'):
                residual_company_signed += line.amount_residual
                if line.currency_id == self.currency_id:
                    residual += line.amount_residual_currency if line.currency_id else line.amount_residual
                else:
                    from_currency = (line.currency_id and line.currency_id.with_context(date=line.date)) or line.company_id.currency_id.with_context(date=line.date)
                    residual += from_currency.compute(line.amount_residual, self.currency_id)
      
	    # Resiaul calculated for credit note

        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual)
        digits_rounding_precision = self.currency_id.rounding


        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False

