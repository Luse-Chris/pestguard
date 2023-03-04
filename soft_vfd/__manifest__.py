# -*- coding: utf-8 -*-
{
    'name': "soft_vfd",

    'summary': """
        An online solution for business owners to issue TRA Receipts without the need of an EFD Machine.
        """,

    'description': """
       An online solution for business owners to issue TRA Receipts without the need of an EFD Machine.
    """,

    'author': "Softnet Technologies",
    'website': "http://softnet.co.tz",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account','point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
         "views/pos_config_views.xml",
        # "views/pos_order_views.xml",
        'views/vfd_vfd_views.xml',
        'views/vfd_receipt_views.xml',
        'views/vfd_zreport_views.xml',
        'views/account_move_inherit.xml',
        'views/account_tax_inherit.xml',
        'views/res_partner_views.xml',
        'data/sequence.xml',
        "data/ir_cron_data.xml",
        "report/invoice_report.xml",
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "assets": {
        "point_of_sale.assets": [
            "soft_vfd/static/src/js/Screens/ReceiptScreen/OrderReceipt.js",
            "soft_vfd/static/src/js/Screens/ReceiptScreen/VFDOrderReceipt.js",
            # "soft_vfd/static/src/js/Screens/ClientListScreen/ClientDetailsEdit.js",
            # "soft_vfd/static/src/js/Screens/ClientListScreen/ClientListScreen.js",
            "soft_vfd/static/src/js/Screens/PaymentScreen/PaymentScreen.js",
            #    "soft_vfd/static/src/js/models.js",
            "soft_vfd/static/src/css/pos_receipts.css",
            "soft_vfd/static/src/xml/Screens/ReceiptScreen/OrderReceipt.xml",
            "soft_vfd/static/src/xml/Screens/ReceiptScreen/VFDOrderReceipt.xml",
        ],
        "web.assets_qweb": [
           
            # "soft_vfd/static/src/xml/Screens/ClientListScreen/ClientDetailsEdit.xml"
        ],
    },
}
