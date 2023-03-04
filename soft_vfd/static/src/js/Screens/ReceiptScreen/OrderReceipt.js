odoo.define("pos_soft_vfd.OrderReceipt", function (require) {
    'use strict';
    console.log("loaded: pos_soft_vfd.OrderReceipt")
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const VFDOrderReceipt = (OrderReceipt) =>
        class extends OrderReceipt {
            get isVFDEnable() {
                return this.env.pos.config.is_vfd_enabled
            }
            /* 
              VFD receipt should be printed only when vfd device is enabled 
              in the pos configuration and isBill should be false
            */
            get isPrintVFDReceiptEnabled(){
                const res = this.isVFDEnable && !this.props.isBill
                return res
    
            }
        }
    Registries.Component.extend(OrderReceipt, VFDOrderReceipt);
    return VFDOrderReceipt;
})