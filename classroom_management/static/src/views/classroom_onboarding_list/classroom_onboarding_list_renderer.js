// classroom_management/static/src/views/classroom_onboarding_list/classroom_onboarding_list_renderer.js
import { ListRenderer } from "@web/views/list/list_renderer";
import { ClassroomActionHelper } from "../../js/classroom_action_helper/classroom_action_helper";

export class ClassroomListRenderer extends ListRenderer {
    static template = "classroom_management.ClassroomListRenderer";
    static components = {
        ...ListRenderer.components,
        ClassroomActionHelper,
    };

    get showNoContentHelper() {
        //console.log("Current companyId in renderer:", this.props.list._config.currentCompanyId);
        return super.showNoContentHelper;
    }
}
