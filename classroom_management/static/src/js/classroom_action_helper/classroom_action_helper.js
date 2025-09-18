import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ClassroomActionHelper extends Component {
    static template = "classroom_management.ClassroomActionHelper";
    static props = {
        list: Object,
        noContentHelp: String,
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            showOnboarding: true,
            completedSteps: [],
            steps: [
                {
                    id: 1,
                    model: "mc.grade.distribution",
                    title: "Configure Grade Distribution",
                    description: "Start by stating the grade distribution.",
                    action: "openGradeDistributionForm",
                    icon: "/classroom_management/static/src/img/onboarding_cog.png",
                    button:"Add distribution"
                },
                {
                    id: 2,
                    model: "education.syllabus",
                    title: "Add Syllabus",
                    description: "Start by adding syllabus for the school",
                    action: "openSyllabusForm",
                    icon: "/classroom_management/static/src/img/onboarding_cog.png",
                    button:"Add syllabus"
                },
            ],
        });
        onWillStart(() => this.checkAndInitialize());
    }

    async checkAndInitialize() {
        try {
            const companyId = this.props.list._config.currentCompanyId;
            console.log("Using companyId from list:", companyId);
            if (!companyId) {
                this.state.showOnboarding = true;
                return;
            }
            const domain = [["company_id", "=", companyId]];
            const [evalCount, gdCount, sylCount] = await Promise.all([
                this.orm.searchCount("mc.evaluation.grades", domain),
                this.orm.searchCount("mc.grade.distribution", domain),
                this.orm.searchCount("education.syllabus", domain),
            ]);

            if (evalCount > 0 || (gdCount > 0 && sylCount > 0)) {
                this.state.showOnboarding = false;
                return;
            }

            this.state.completedSteps = [];
            if (gdCount > 0) this.state.completedSteps.push(1);
            if (sylCount > 0) this.state.completedSteps.push(2);

            if (this.state.completedSteps.length === this.state.steps.length) {
                this.state.showOnboarding = false;
            }
        } catch (error) {
            console.error("Error in checkAndInitialize:", error);
            this.state.showOnboarding = true;
            this.state.completedSteps = [];
        }
    }

    get progressPercentage() {
        return (this.state.completedSteps.length / this.state.steps.length) * 100;
    }

    async checkStepCompletion(stepId, model) {
        const companyId = this.props.list._config.currentCompanyId;
        const domain = [["company_id", "=", companyId]];
        const count = await this.orm.searchCount(model, domain);
        if (count > 0 && !this.state.completedSteps.includes(stepId)) {
            this.state.completedSteps.push(stepId);
            if (this.state.completedSteps.length === this.state.steps.length) {
                this.state.showOnboarding = false;
            }
        }
    }

    openGradeDistributionForm() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Grade Distribution",
            res_model: "mc.grade.distribution",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            context: { form_view_ref: "mc.grade.distribution_form_view" }, // Ensure correct form view
        }, {
            onClose: async () => {
                await this.checkStepCompletion(1, "mc.grade.distribution");
            },
        });
    }

    openSyllabusForm() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Syllabus",
            res_model: "education.syllabus",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            context: { form_view_ref: "education.syllabus_form_view" }, // Ensure correct form view
        }, {
            onClose: async () => {
                await this.checkStepCompletion(2, "education.syllabus");
            },
        });
    }

    executeStepAction(step) {
        if (!step) return;

        // If step is completed, open the list view
        if (this.isStepCompleted(step.id)) {
            this.actionService.doAction({
                type: "ir.actions.act_window",
                name: step.title,
                res_model: step.model,
                view_mode: "list,form",
                views: [[false, "list"]],
                domain: [["company_id", "=", this.props.list._config.currentCompanyId]],
                target: "new",
            });
        }
        // Otherwise, execute the form action
        else if (this[step.action]) {
            this[step.action]();
        }
    }

    markStepCompleted(stepId) {
        if (!this.state.completedSteps.includes(stepId)) {
            this.state.completedSteps.push(stepId);
        }
        if (this.state.completedSteps.length === this.state.steps.length) {
            this.state.showOnboarding = false;
        }
    }

    skipStep(stepId) {
        this.markStepCompleted(stepId);
    }

    isStepCompleted(stepId) {
        return this.state.completedSteps.includes(stepId);
    }
}