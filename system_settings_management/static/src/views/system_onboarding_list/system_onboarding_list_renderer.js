/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { SystemActionHelper } from "../../js/system_settings_action_helper/system_settings_action_helper";

export class SystemListRenderer extends ListRenderer {
    static template = "system_settings_management.SystemListRenderer";
    static components = {
        ...ListRenderer.components,
        SystemActionHelper,
    };
}