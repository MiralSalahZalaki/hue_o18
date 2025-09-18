/** @odoo-module **/
// classroom_management/static/src/views/classroom_onboarding_list/classroom_onboarding_list_view.js
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ClassroomListRenderer } from "./classroom_onboarding_list_renderer";

export const classroomOnboardingListView = {
    ...listView,
    Renderer: ClassroomListRenderer,
};

registry.category("views").add("classroom_onboarding_list", classroomOnboardingListView);