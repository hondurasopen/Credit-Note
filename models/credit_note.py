# -*- encoding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
import base64
import csv
import cStringIO
from odoo.exceptions import except_orm, Warning, RedirectWarning


class CreditNote(models.TransientModel):
    _name = "credit.note"

    @api.model
    def _get_date(self):
        ctx = self._context
        if 'active_id' in ctx:
            inv = self.env['account.invoice'].browse(ctx['active_id'])
            return inv.date_invoice

    @api.model
    def _get_amount(self):
        ctx = self._context
        if 'active_id' in ctx:
            inv = self.env['account.invoice'].browse(ctx['active_id'])
            return inv.residual
        else:
            return 0.00

    @api.model
    def _get_invoice_number(self):
        ctx = self._context
        if 'active_id' in ctx:
            inv = self.env['account.invoice'].browse(ctx['active_id'])
            return inv.number
        else:
            raise except_orm(_('Warning'), _('!! Invoice is draft, Invoice must be in validate state!!'))


    date_note = fields.Date(string="Date of Credit Note", required=True, default=_get_date)
    journal_id = fields.Many2one('account.journal', 'Journal of Credit Note', required=True, domain=[('type', '=', 'sale')])
    name = fields.Char(string="Description of Credit Note", required=True)
    amount = fields.Float("Amount", required=True, default=_get_amount)
    invoice_number = fields.Char("Invoice number", readonly=True, default=_get_invoice_number)

    _defaults = {
        'date_note': _get_date,
        'amount': _get_amount,
        'invoice_number': _get_invoice_number,
   	 }

    @api.one
    def invoice_credit_note(self):
        obj_refund = self.env["account.invoice"]
        inv_line_obj = self.env['account.invoice.line']
        active_id = self._context.get('active_id')
        qty = 1
        credit_note_number = self.journal_id.sequence_id.number_next_actual

        if active_id:
            inv = self.env['account.invoice'].browse(active_id)

            if inv.residual < 0:
                raise except_orm(_('Warning'), _('!! Amount must be greater than zero !!'))

            if self.amount > inv.residual:
                raise except_orm(_('Warning'), _('!! Amount is greater than Invoice Total !!'))

            movelines = inv.move_id.line_ids
            to_reconcile_ids = {}
            to_reconcile_lines = self.env['account.move.line']
            for line in movelines:
                if line.account_id.id == inv.account_id.id:
                    to_reconcile_lines += line
                    to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                if line.reconciled:
                    line.remove_move_reconcile()
            values = {
                'partner_id': inv.partner_id.id,
                'date_invoice': self.date_note,
                'account_id': inv.account_id.id,
                'type': 'out_refund',
                'number': credit_note_number,
                'journal_id': self.journal_id.id,
                'origin': self.invoice_number,
                'name': self.name,
            }

            invoice_id = obj_refund.create(values)
            inv_line_id = False
            if invoice_id:
                vals = {
                    'name': self.name,
                    'invoice_id': invoice_id.id,
                    'account_id': self.journal_id.default_debit_account_id.id,
                    'price_unit': self.amount,
                    'quantity': qty,
                    }
                inv_line_id = inv_line_obj.create(vals)
            if invoice_id and inv_line_id:
                new_residual = inv.residual - self.amount
                inv.write({'residual': new_residual, 'residual_signed': new_residual})
                #date_assigned = invoice_id.action_date_assign()
                #move_created = invoice_id.action_move_create()
                #number_asigned = invoice_id.action_number()
                #validated = invoice_id.invoice_validate()
                invoice_id.action_invoice_open()
                for tmpline in invoice_id.move_id.line_ids:
                    if tmpline.account_id.id == inv.account_id.id:
                        to_reconcile_lines += tmpline
                        to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                if inv.residual <= 0:
                    inv.write({'state': 'paid'})
        else:
            raise except_orm(_('Warning'), _('!! Credit note cannot be create !!'))
