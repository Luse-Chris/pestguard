odoo.define('pos_soft_vfd.models', function (require) {
    "use strict";
    var models = require("point_of_sale.models");
    models.load_fields("res.partner",["id_type", "nida","tin","driving_license","voters_number","passport", "vrn"]);

})