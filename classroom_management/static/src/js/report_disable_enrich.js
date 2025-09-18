/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ReportAction } from "@web/webclient/actions/reports/report_action";

patch(ReportAction.prototype, {
    async _enrichHtml() {
        // Skip enrichment completely
        return Promise.resolve();
    },
});
