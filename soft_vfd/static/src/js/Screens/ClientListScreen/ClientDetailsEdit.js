odoo.define("pos_soft_vfd.ClientDetailsEdit", function (require) {
    'use strict';
    const Registries = require('point_of_sale.Registries');
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const VFDClientDetailsEdit = (ClientDetailsEdit) =>
        class extends ClientDetailsEdit {
            captureChange(event) {
                this.changes[event.target.name] = event.target.value;
                this.render()
            }
            get customerIdTypes (){
                return [
                    {
                        "value": "1",
                        "label": "TIN"
                    },
                    {
                        "value": "2",
                        "label": "Driving Licence"
                    },
                    {
                        "value": "3",
                        "label": "Voter Number"
                    },
                    {
                        "value": "4",
                        "label": "Passport"
                    },
                    {
                        "value": "5",
                        "label": "National Identity (NID)"
                    },

                ]
            }
            mounted() {
                this.env.bus.on('save-customer', this, this.saveChanges);
            }
        }
    Registries.Component.extend(ClientDetailsEdit, VFDClientDetailsEdit);
    return VFDClientDetailsEdit;
})