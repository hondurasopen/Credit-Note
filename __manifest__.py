# -*- coding: utf-8 -*-
{
"name":"Credit Note",
"author": "Alejandro Rodriguez, Honduras Open Source",
"description": "This Module creates Credit Note on Invoices",
"category":"Sale",
"depends":["base",
           "sale",
		      "account"
],
 "data": [
 		"views/nota_debito_view.xml",
 		"views/account_nota_debito.xml",
 		"views/credit_note_inv_view.xml",
	    "views/account_credit_note.xml",
        ],
'update_xml' : [
        'security/groups.xml',
        'security/ir.model.access.csv'
],
"auto_install": False,
"installable": True,
}
