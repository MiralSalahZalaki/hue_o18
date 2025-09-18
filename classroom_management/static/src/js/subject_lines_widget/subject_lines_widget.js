/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class SubjectLinesWidget extends Component {
  static template = "classroom_management.SubjectLinesWidget";
  static props = {
    ...standardFieldProps,
  };

  setup() {
    this.orm = useService("orm");
    this.state = useState({
      subjectLines: [],
      systemType: "general",
    });

    onWillStart(async () => {
      await this.loadSystemType();
      await this.loadSubjectLines();
    });

    onWillUpdateProps(async (nextProps) => {
      // Prevent reload action in every time user select page of (widget)
      const currentResId = nextProps.record.model.config.resId;
      const nextResId = nextProps.record.evalContext.id;

      await this.loadSubjectLines();
    });
  }

  /**
   * Load system type for current company
   */
  async loadSystemType() {
    try {
      const companyId = this.props.record.data.company_id?.[0];
      if (!companyId) {
        this.state.systemType = "general";
        return;
      }

      const systemSettings = await this.orm.searchRead(
        "system.settings",
        [["company_id", "=", companyId]],
        ["system_type"],
        { limit: 1 }
      );

      this.state.systemType =
        systemSettings.length > 0 ? systemSettings[0].system_type : "general";
    } catch (error) {
      console.error("Error loading system type:", error);
      this.state.systemType = "general";
    }
  }

  /**
   * Determine the model type and return appropriate model names
   */
  getModelNames() {
    const currentModel = this.props.record.resModel;

    if (currentModel === "acc.student.term.grades") {
      return {
        subjectLineModel: "acc.student.term.subject.line",
        assessmentLineModel: "acc.student.term.subject.assessment.line",
        distributionLineModel: "acc.student.term.subject.distribution.line",
        isTermModel: true,
        isMonthlyModel: false,
      };
    } else if (currentModel === "acc.student.monthly.grades") {
      return {
        subjectLineModel: "acc.student.monthly.subject.line",
        assessmentLineModel: "acc.student.monthly.subject.assessment.line",
        distributionLineModel: null, // Monthly doesn't have distribution lines
        isTermModel: false,
        isMonthlyModel: true,
      };
    } else {
      // Fallback to term model if unknown
      return {
        subjectLineModel: "acc.student.term.subject.line",
        assessmentLineModel: "acc.student.term.subject.assessment.line",
        distributionLineModel: "acc.student.term.subject.distribution.line",
        isTermModel: true,
        isMonthlyModel: false,
      };
    }
  }

  async loadSubjectLines() {
    if (
      !this.props.record.data.subject_line_ids ||
      this.props.record.data.subject_line_ids.length === 0
    ) {
      this.state.subjectLines = [];
      return;
    }

    try {
      const modelNames = this.getModelNames();

      // Base fields for both models
      let baseFields = [
        "id",
        "syllabus_id",
        "assessment_line_ids",
        "total_subject_score",
        "total_subject_max",
        "grading_info",
        "grading_method",
      ];

      // Add British system fields if it's a term model
      if (modelNames.isTermModel) {
        baseFields = [
          ...baseFields,
          "british_monthly",
          "british_weekly",
          "british_exam",
          "british_total",
          "british_monthly_max",
          "british_weekly_max",
          "british_exam_max",
          "british_total_max",
        ];
      }

      // Add distribution_line_ids only for term model
      const fieldsToRead = modelNames.isTermModel
        ? [...baseFields, "distribution_line_ids"]
        : baseFields;

      const subjectLines = await this.orm.searchRead(
        modelNames.subjectLineModel,
        [["parent_id", "=", this.props.record.model.config.resId]],
        fieldsToRead
      );

      for (const line of subjectLines) {
        // Get syllabus name
        if (line.syllabus_id && line.syllabus_id.length > 0) {
          line.syllabus_name =
            line.syllabus_id[1] ||
            (await this.getSyllabusName(line.syllabus_id[0]));
        } else {
          line.syllabus_name = "Unknown Subject";
        }

        // For British system, skip loading assessment and distribution lines
        if (
          this.state.systemType === "british" &&
          line.grading_method === "numeric" &&
          modelNames.isTermModel
        ) {
          line.assessment_lines = [];
          line.distribution_lines = [];
        } else {
          // Load assessment lines for non-British systems
          line.assessment_lines = await this.orm.searchRead(
            modelNames.assessmentLineModel,
            [["parent_id", "=", line.id]],
            [
              "id",
              "assessment_id",
              "max_score",
              "score",
              "assessment_name",
              "description",
            ]
          );

          // Load distribution lines only for term model and non-British systems
          if (modelNames.isTermModel && modelNames.distributionLineModel) {
            line.distribution_lines = await this.orm.searchRead(
              modelNames.distributionLineModel,
              [["parent_id", "=", line.id]],
              [
                "id",
                "distribution_id",
                "max_score",
                "score",
                "distribution_name",
                "check",
                "description",
              ]
            );
          } else {
            // For monthly model, set empty distribution lines
            line.distribution_lines = [];
          }
        }

        // Add model type info for template usage
        line.modelType = {
          isTermModel: modelNames.isTermModel,
          isMonthlyModel: modelNames.isMonthlyModel,
        };
      }

      this.state.subjectLines = subjectLines;
    } catch (error) {
      console.error("Error loading subject lines:", error);
      this.state.subjectLines = [];
    }
  }

  async getSyllabusName(syllabusId) {
    try {
      const syllabus = await this.orm.read(
        "education.syllabus",
        [syllabusId],
        ["name"]
      );
      return syllabus[0]?.name || "Unknown Subject";
    } catch (error) {
      console.error("Error getting syllabus name:", error);
      return "Unknown Subject";
    }
  }

  /**
   * Helper method to check if current model is term model
   */
  isTermModel() {
    return this.getModelNames().isTermModel;
  }

  /**
   * Helper method to check if current model is monthly model
   */
  isMonthlyModel() {
    return this.getModelNames().isMonthlyModel;
  }

  /**
   * Get the display title based on model type
   */
  getDisplayTitle() {
    const modelNames = this.getModelNames();
    if (modelNames.isTermModel) {
      return "Term Subject Lines";
    } else if (modelNames.isMonthlyModel) {
      return "Monthly Subject Lines";
    }
    return "Subject Lines";
  }
}

registry.category("fields").add("subject_lines_widget", {
  component: SubjectLinesWidget,
});
