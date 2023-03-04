odoo.define("pos_soft_vfd.ClientListScreen", function (require) {
    'use strict';
    const Registries = require('point_of_sale.Registries');
    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const VFDClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            async saveChanges(event) {
            
                try {

                    // Validate VRN
                    const processedChanges = event.detail.processedChanges
                    if (processedChanges?.["vrn"] && !processedChanges["vrn"].match(/\d{8}[A-Z]$/)) {
                        return this.showPopup('ErrorPopup', {
                            title: this.env._t('Error: VRN Format.'),
                            body: this.env._t('Invalid VRN Format (ex. 12345678G)')
                        });
                    }
                    // Validate Customer Tin number
                    if (processedChanges?.["tin"] && !processedChanges["tin"].match(/^\d{9}$/)){
                         return this.showPopup('ErrorPopup', {
                                title: this.env._t('Error: Invalid Tin number.'),
                             body: this.env._t('Invalid Tin Number Format (ex. xxx-xxx-xxx)')
                            });
                    }
                    // Validate Customer voters number
                    if (processedChanges?.["voters_number"] && !processedChanges["voters_number"].match(/T-(?:\d{4}-){2}\d{3}-\d$/)) {
                        return this.showPopup('ErrorPopup', {
                            title: this.env._t('Error: Invalid Voter number.'),
                            body: this.env._t('Invalid Voter Number Format (ex. T-2000-7659-212-4)')
                        });
                    }
                    // Validate nida number
                    if (processedChanges?.["nida"] && !processedChanges["nida"].match(/([12]\d{3}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])-\d{5}-\d{5}-\d{2}$)/)) {
                        return this.showPopup('ErrorPopup', {
                            title: this.env._t('Error: Invalid National Identification Number.'),
                            body: this.env._t('Invalid National Identification Number(NID) Format (ex. 19201220-12345-00001-12)')
                        });
                    }
                    let partnerId = await this.rpc({
                        model: 'res.partner',
                        method: 'create_from_ui',
                        args: [event.detail.processedChanges],
                    });
                    await this.env.pos.load_new_partners();
                    this.state.selectedClient = this.env.pos.db.get_partner_by_id(partnerId);
                    this.state.detailIsShown = false;
                    this.render();
                } catch (error) {
                    if (error?.message?.code < 0) {
                        await this.showPopup('OfflineErrorPopup', {
                            title: this.env._t('Offline'),
                            body: this.env._t('Unable to save changes.'),
                        });
                    } else {
                        throw error;
                    }
                }
            }
      
    
        }
    Registries.Component.extend(ClientListScreen, VFDClientListScreen);
    return VFDClientListScreen
})