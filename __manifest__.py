# -*- coding: utf-8 -*-
{
"name":"Credit Note",
"author": "Alejandro Rodriguez, Honduras Open Source",
"description": "This Module creates credit Note and debit note on Invoices",
"category":"Sale",
"depends":["base",
           "sale",
		      "account"
],
 "data": [
 		'security/groups.xml',
        'security/ir.model.access.csv',
 		"views/nota_debito_view.xml",
 		"views/account_nota_debito.xml",
 		"views/credit_note_inv_view.xml",
	    "views/account_credit_note.xml",
        ],
"auto_install": False,
"installable": True,
}
