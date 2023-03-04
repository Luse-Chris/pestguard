odoo.define('pos_soft_vfd.VFDOrderReceipt', function (require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const { onMounted } = owl;

    class VFDOrderReceipt extends PosComponent {
        setup() {
            super.setup();
            this.state = {
                receipt:  undefined,
            }
            onMounted(() =>{
                // Fetch vfd receipt from the server
                this.fetchCurrentVFDReceipt().then((receipt) => {
                    this.state.receipt = receipt
                    this.render()
                }).catch((err) => {
                    console.log(err)
                    console.log(`Failed to fetch Current VFD Receipt`)
                    this.render()
                })
            })
        }
        async fetchCurrentVFDReceipt(){
            let order_server_id
            if (this.props.order.backendId){
                // reprint receipts
                order_server_id = this.props.order.backendId
            }else{
                const orderName = this.currentOrder.get_name();
                order_server_id = this.env.pos.validated_orders_name_server_id_map[orderName];
            }
          
            this.state.loading = true
            this.render()
            const res = await rpc.query({
                model: 'pos.order',
                method: 'get_posted_receipt',
                args: [[order_server_id]],
            });
            return res
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
        get qrcodeUrl(){
            return `https://api.qrserver.com/v1/create-qr-code/?data=${this.state.receipt.qrcode}&amp;size=100x100`
        }
    }

    VFDOrderReceipt.template = 'VFDOrderReceipt';
    Registries.Component.add(VFDOrderReceipt);
    return VFDOrderReceipt;

})