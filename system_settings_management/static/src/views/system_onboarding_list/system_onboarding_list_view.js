/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { SystemListRenderer } from "./system_onboarding_list_renderer";

export const systemOnboardingListView = {
    ...listView,
    Renderer: SystemListRenderer,
};

registry.category("views").add("system_onboarding_list", systemOnboardingListView);
