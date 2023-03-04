odoo.define("pos_soft_vfd.PaymentScreen", function (require) {
    'use strict';
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const VFDPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            get isVFDEnable() {
                return this.env.pos.config.is_vfd_enabled
            }
            /* 
              Overide validate Order to add extra validation
              The goal is to make sure if vfd is enable all order lines
              should have only one tax.
              I
            */
            async validateOrder(isForceValidate) {
                let has_error = false;
                for (let [index, line] of this.env.pos.get_order().get_orderlines().entries()){
                    const hasTax = !!line.tax_ids?.length || line.product.taxes_id.length > 0
                    if (this.isVFDEnable && !hasTax){
                        this.showPopup('ErrorPopup', {
                            title: this.env._t(`Missing Tax in order line #${index}`),
                            body: this.env._t(`No taxes found for product ${line.product.display_name} in #${index}`),
                        });
                        has_error = true
                        break;
                    }
                }
                if (has_error) return;
                if (this.env.pos.config.cash_rounding) {
                    if (!this.env.pos.get_order().check_paymentlines_rounding()) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Rounding error in payment lines'),
                            body: this.env._t("The amount of your payment lines must be rounded to validate the transaction."),
                        });
                        return;
                    }
                }
                if (await this._isOrderValid(isForceValidate)) {
                    // remove pending payments before finalizing the validation
                    for (let line of this.paymentLines) {
                        if (!line.is_done()) this.currentOrder.remove_paymentline(line);
                    }
                    await this._finalizeValidation();
                }
            }
        }
    Registries.Component.extend(PaymentScreen, VFDPaymentScreen);
    return VFDPaymentScreen;
})