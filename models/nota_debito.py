# -*- encoding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning


class Notadebito(models.TransientModel):
    _name = "nota.debito.factura"

    @api.model
    def _get_invoice_number(self):
        ctx = self._context
        if 'active_id' in ctx:
            inv = self.env['account.invoice'].browse(ctx['active_id'])
            return inv.number
        else:
            raise except_orm(_('Warning'), _('!! Invoice is draft, Invoice must be in validate state!!'))

    fecha_nota = fields.Date(string="Fecha de Inicio", required=True)
    journal_id = fields.Many2one('account.journal', 'Diario Nota de Debito', required=True, domain=[('type', '=', 'sale')])
    name = fields.Char(string="Motivo Nota de Debito", required=True)
    amount = fields.Float("Monto aplicar", required=True)
    invoice_number = fields.Char("# de Factura", readonly=True, default=_get_invoice_number)


    @api.one
    def invoice_nota_debito(self):
        journal_id = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        obj_debit = self.env["account.invoice"]
        inv_line_obj = self.env['account.invoice.line']
        active_id = self._context.get('active_id')
        qty = 1
        number_dedit_note = journal_id.sequence_id.number_next_actual
        if active_id:
            inv = self.env['account.invoice'].browse(active_id)
            if inv.residual < 0:
                raise except_orm(_('Warning'), _('!! Amount must be greater than zero !!'))

            values={
                'partner_id': inv.partner_id.id,
                'date_invoice': self.fecha_nota,
                'account_id': inv.partner_id.property_account_receivable_id.id,
                'type': 'out_invoice',
                'journal_id': self.journal_id.id,
                'origin': self.invoice_number,
                'nota_debito': True,
                'state': 'draft',
                }
            invoice_id = obj_debit.create(values)
            if invoice_id:
                vals={
                    'name': self.name,
                    'invoice_id': invoice_id.id,
                    'account_id': self.journal_id.default_debit_account_id.id,
                    'price_unit': self.amount,
                    'quantity': qty,
                }
                inv_line_id = inv_line_obj.create(vals)
        else:
            raise except_orm(_('Advertencia'), _('.No se puede crear nota de dedito, consulte el administrador del sistema!!'))

