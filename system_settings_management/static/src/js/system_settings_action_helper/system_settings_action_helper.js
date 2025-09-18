/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class SystemActionHelper extends Component {
  static template = "system_settings_management.SystemActionHelper";
  static props = {
    list: { type: Object, optional: true },
    noContentHelp: { type: String, optional: true },
  };

  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.notification = useService("notification");
    this.companyService = useService("company");

    this.state = useState({
      showOnboarding: true,
      hasContent: false,
      hasCompanies: false,
      allCompanies: [],
      companyNames: {}, // لتخزين أسماء الشركات
      companiesCount: 0,
      settingsCount: 0,
      currentCompanyId: null, // سيكون دايما الشركة الحالية
      currentCompanyName: "",
      currentTab: 1,
      totalTabs: 1,
      steps: [
        {
          id: 1,
          model: "res.company",
          title: "Add Company",
          description: "Start by adding your school/company info.",
          action: "openCompanyForm",
          icon: "/system_settings_management/static/src/img/onboarding_company.png",
          button: "Add Company",
          complete_state: false,
          complete_msg: "✅ Company added!",
        },
        {
          id: 2,
          model: "mc.education.stages",
          title: "Add Education Stages",
          description: "Set the educational stages in your school.",
          action: "openStageForm",
          icon: "/system_settings_management/static/src/img/stage.png",
          button: "Add Stages",
          complete_state: false,
          complete_msg: "✅ Stage added!",
          hasImport: true,
        },
        {
          id: 3,
          model: "education.class",
          title: "Add Grades to your company",
          description: "Start by adding your grades info.",
          action: "openGradeForm",
          icon: "/system_settings_management/static/src/img/onboarding_grades.png",
          button: "Add Grades",
          complete_state: false,
          complete_msg: "✅ Grade added!",
          hasImport: true,
        },
        {
          id: 4,
          model: "education.academic.year",
          title: "Academic Year Setup",
          description: "Define start & end dates for the academic year.",
          action: "openYearForm",
          icon: "/system_settings_management/static/src/img/onboarding_accounting-periods.png",
          button: "Add Years",
          complete_state: false,
          complete_msg: "✅ Years added!",
          hasImport: true,
        },
        {
          id: 5,
          model: "education.division",
          title: "Add Standard Division",
          description: "Create divisions to manage academic structure",
          action: "openDivisionForm",
          icon: "/system_settings_management/static/src/img/division.png",
          button: "Add Divisions",
          complete_state: false,
          complete_msg: "✅ Divisions added!",
          hasImport: true,
        },
        {
          id: 6,
          model: "mc.religion",
          title: "Define Religion",
          description: "Add the religion data",
          action: "openReligionForm",
          icon: "/system_settings_management/static/src/img/onboarding_company.png",
          button: "Set Religion",
          complete_state: false,
          complete_msg: "✅ Done!",
          hasImport: true,
        },
        {
          id: 7,
          model: "student.ldap.directory",
          title: "LDAP Directory",
          description: "Define LDAP Directory for Students",
          action: "openLdapForm",
          icon: "/system_settings_management/static/src/img/onboarding_company.png",
          button: "Add LDAP",
          complete_state: false,
          complete_msg: "✅ Done!",
          hasImport: true,
        },
        {
          id: 8,
          model: "mc.rooms",
          title: "Rooms",
          description: "Define Rooms for Classes",
          action: "openRoomForm",
          icon: "/system_settings_management/static/src/img/onboarding_company.png",
          button: "Add Rooms",
          complete_state: false,
          complete_msg: "✅ Done!",
          hasImport: true,
        },
        {
          id: 9,
          model: "education.class.division",
          title: "Add Class divisions",
          description: "Let's add your class divisions.",
          action: "openClassDivisionForm",
          icon: "/system_settings_management/static/src/img/onboarding_grades.png",
          button: "Add Divisions",
          complete_state: false,
          complete_msg: "✅ Class divisions added!",
          hasImport: true,
        },
        /* {
                    id: 10,
                    model: "education.application",
                    title: "Add Student Applications",
                    description: "Add Studnt Applications.",
                    action: "openApplicationForm",
                    icon: "/system_settings_management/static/src/img/onboarding_grades.png",
                    button: "Add Student Applications",
                    complete_state: false,
                    complete_msg: "✅Applications added!",
                    hasImport: true
                },
                {
                    id: 11,
                    model: "education.student",
                    title: "Add Student Record",
                    description: "Add Studnt.",
                    action: "openStudentForm",
                    icon: "/system_settings_management/static/src/img/onboarding_grades.png",
                    button: "Add Student Record",
                    complete_state: false,
                    complete_msg: "Students added!",
                    hasImport: true
                }, */
      ],
    });
    onWillStart(() => this.checkAndInitialize());
  }

  async checkAndInitialize() {
    try {
      const company_ids = await this.orm.search("res.company", []);
      this.state.allCompanies = company_ids;
      this.state.companiesCount = company_ids.length;
      this.state.hasCompanies = company_ids.length > 0;
      this.state.totalTabs = Math.ceil(this.state.steps.length / 3);

      // تحميل أسماء جميع الشركات مرة واحدة
      if (company_ids.length > 0) {
        await this.loadAllCompanyNames();

        // تعيين الشركة الحالية من companyService
        this.state.currentCompanyId = this.companyService.currentCompany.id;
        this.state.currentCompanyName = this.companyService.currentCompany.name;
      }

      if (company_ids.length === 0) {
        this.state.showOnboarding = true;
        this.state.steps[0].complete_state = false;
        this.state.steps[1].complete_state = false;
        this.state.steps[2].complete_state = false;
        this.state.steps[3].complete_state = false;
        this.state.currentCompanyId = null;
        this.state.currentCompanyName = "";
      } else {
        // فحص أي الشركات محتاجة إعداد
        const grades = await this.orm.searchRead(
          "education.class",
          [["school", "!=", false]],
          ["school"]
        );
        const schools_with_grades = [
          ...new Set(grades.map((g) => g.school[0])),
        ];
        const companies_without_grades = company_ids.filter(
          (id) => !schools_with_grades.includes(id)
        );

        if (companies_without_grades.length > 0) {
          this.state.showOnboarding = true;
          this.state.steps[0].complete_state = true;
          this.state.steps[1].complete_state = false;
          this.state.steps[2].complete_state = false;
          this.state.steps[3].complete_state = false;
        } else {
          this.state.showOnboarding = false;
          this.state.steps[0].complete_state = true;
          this.state.steps[1].complete_state = true;
          this.state.steps[2].complete_state = true;
          this.state.steps[3].complete_state = true;
        }
      }
    } catch (error) {
      console.error("Error checking initialization:", error);
      this.state.showOnboarding = true;
    }
  }

  async loadAllCompanyNames() {
    try {
      if (this.state.allCompanies.length > 0) {
        const companies = await this.orm.read(
          "res.company",
          this.state.allCompanies,
          ["name"]
        );
        const companyNames = {};
        companies.forEach((company) => {
          companyNames[company.id] = company.name;
        });
        this.state.companyNames = companyNames;
      }
    } catch (error) {
      console.error("Error loading company names:", error);
    }
  }

  getCurrentStepGroup() {
    const startIndex = (this.state.currentTab - 1) * 3;
    const endIndex = startIndex + 3;
    return this.state.steps.slice(startIndex, endIndex);
  }

  previousTab() {
    if (this.state.currentTab > 1) {
      this.state.currentTab -= 1;
    }
  }

  nextTab() {
    if (this.state.currentTab < this.state.totalTabs) {
      this.state.currentTab += 1;
    }
  }

  // Step 1: Open Company Form
  openCompanyForm() {
    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Add Company",
        res_model: "res.company",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
      },
      {
        onClose: async (result) => {
          if (result && result.res_id) {
            const companyId = result.res_id;
            this.state.companiesCount += 1;

            // تحديث قائمة الشركات وأسمائها
            this.state.allCompanies.push(companyId);
            await this.loadAllCompanyNames();

            // تحديث الشركة الحالية (ستبقى كما هي من companyService)
            this.state.currentCompanyId = this.companyService.currentCompany.id;
            this.state.currentCompanyName =
              this.companyService.currentCompany.name;

            this.state.steps[0].complete_state = true;
            this.notification.add(
              "Company created successfully! Now you can add stages to it.",
              { title: "Great! Next Step", type: "success" }
            );
          }
          await this.checkAndInitialize();
        },
      }
    );
  }

  // Step 2: Open Stage Form
  async openStageForm() {
    let companyId = this.state.currentCompanyId;

    if (!companyId) {
      const company_ids = await this.orm.search("res.company", []);
      if (company_ids.length === 0) {
        this.notification.add("No company available for stages creation.", {
          title: "Add Company first",
          type: "danger",
        });
        return;
      }
      companyId = company_ids[0];
      this.state.currentCompanyId = companyId;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Add Educational Stages",
        res_model: "mc.education.stages",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
        context: {
          default_company_id: companyId,
          readonly_company_id: true,
        },
      },
      {
        onClose: async (result) => {
          if (result && result.res_id) {
            this.notification.add(
              "Educational stage created successfully! Now add grades.",
              { title: "Great! Next Step", type: "success" }
            );
          }
          await this.checkAndInitialize();
        },
      }
    );
  }

  // Step 3: Open Grade Form
  async openGradeForm() {
    const companyId = this.state.currentCompanyId;
    if (!companyId) {
      this.notification.add("No company selected for grade creation.", {
        title: "Add Company first",
        type: "danger",
      });
      return;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Add Grades to the company",
        res_model: "education.class",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
        context: { default_school: companyId },
        domain: [["school", "=", companyId]],
      },
      {
        onClose: async () => {
          this.state.steps[2].complete_state = true;
          await this.checkAndInitialize();
        },
      }
    );
  }

  // Step 4: Open Year Form
  async openYearForm() {
    const companyId = this.state.currentCompanyId;
    if (!companyId) {
      this.notification.add("No company selected for Years creation.", {
        title: "Add Company first",
        type: "danger",
      });
      return;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Academic Year Setup",
        res_model: "education.academic.year",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
      },
      {
        onClose: async () => {
          this.state.steps[3].complete_state = true;
          await this.checkAndInitialize();
        },
      }
    );
  }

  // Step 5: Open Division Form
  async openDivisionForm() {
    const companyId = this.state.currentCompanyId;
    if (!companyId) {
      this.notification.add("No company selected for Division creation.", {
        title: "Add Company first",
        type: "danger",
      });
      return;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Division Setup",
        res_model: "education.division",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
      },
      {
        onClose: async () => {
          this.state.steps[4].complete_state = true;
          await this.checkAndInitialize();
        },
      }
    );
  }

  // Step 6: Open Religion Form
  async openReligionForm() {
    const companyId = this.state.currentCompanyId;
    if (!companyId) {
      this.notification.add("No company selected for Religion creation.", {
        title: "Add Company first",
        type: "danger",
      });
      return;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Religions Setup",
        res_model: "mc.religion",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
      },
      {
        onClose: async () => {
          this.state.steps[5].complete_state = true;
          await this.checkAndInitialize();
        },
      }
    );
  }

  // Step 7: Open Ldap Form
  async openLdapForm() {
    const companyId = this.state.currentCompanyId;
    if (!companyId) {
      this.notification.add("No company selected for LDAP creation.", {
        title: "Add Company first",
        type: "danger",
      });
      return;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "LDAP Directory for Students",
        res_model: "student.ldap.directory",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
      },
      {
        onClose: async () => {
          this.state.steps[6].complete_state = true;
          await this.checkAndInitialize();
        },
      }
    );
  }

  // Step 8: Open Room Form
  async openRoomForm() {
    const companyId = this.state.currentCompanyId;
    if (!companyId) {
      this.notification.add("No company selected for Room creation.", {
        title: "Add Company first",
        type: "danger",
      });
      return;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Rooms",
        res_model: "mc.rooms",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
        context: { default_company_id: companyId },
        domain: [],
      },
      {
        onClose: async () => {
          this.state.steps[7].complete_state = true;
          await this.checkAndInitialize();
        },
      }
    );
  }

  // Step 9: Open Division Form
  async openClassDivisionForm() {
    const companyId = this.state.currentCompanyId;
    if (!companyId) {
      this.notification.add("No company selected for division creation.", {
        title: "Add Company first",
        type: "danger",
      });
      return;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Add Class Divisions",
        res_model: "education.class.division",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
        context: { default_school_id: companyId },
        domain: [["school_id", "=", companyId]],
      },
      {
        onClose: async () => {
          this.state.steps[8].complete_state = true;
          await this.checkAndInitialize();
        },
      }
    );
  }

  // Step 10: Open Application Form
  async openApplicationForm() {
    const companyId = this.state.currentCompanyId;
    if (!companyId) {
      this.notification.add("No company selected for division creation.", {
        title: "Add Company first",
        type: "danger",
      });
      return;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Add Student Applications",
        res_model: "education.application",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
        context: { default_company_id: companyId },
        domain: [["company_id", "=", companyId]],
      },
      {
        onClose: async () => {
          this.state.steps[9].complete_state = true;
          await this.checkAndInitialize();
        },
      }
    );
  }

  async openStudentForm() {
    const companyId = this.state.currentCompanyId;
    if (!companyId) {
      this.notification.add("No company selected for division creation.", {
        title: "Add Company first",
        type: "danger",
      });
      return;
    }

    this.actionService.doAction(
      {
        type: "ir.actions.act_window",
        name: "Student Record",
        res_model: "education.student",
        view_mode: "form",
        views: [[false, "form"]],
        target: "new",
        context: { default_company_id: companyId },
        domain: [["company_id", "=", companyId]],
      },
      {
        onClose: async () => {
          this.state.steps[9].complete_state = true;
          await this.checkAndInitialize();
        },
      }
    );
  }

  // تحديث downloadCSVTemplate للتعامل مع company_id الاختياري
  async downloadCSVTemplate(model, modelDisplayName) {
    const companyId = this.state.currentCompanyId; // قد يكون null

    // لا نتطلب company دائماً للتحميل
    if (!companyId) {
      console.warn(
        `No company available for ${modelDisplayName} template. Generating generic template.`
      );
    }

    try {
      // Use csv.handler to get the CSV template
      const result = await this.orm.call(
        "csv.handler",
        "get_csv_template_with_validation",
        [model]
      );

      if (result.success) {
        // Create and download the CSV file
        const blob = new Blob([result.template_content], {
          type: "text/csv;charset=utf-8;",
        });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);

        // تحديث اسم الملف للتعامل مع عدم وجود شركة
        const modelName = modelDisplayName.toLowerCase().replace(/\s+/g, "_");
        const companyName = this.state.currentCompanyName || "no_company";
        const filename = `${modelName}_template_${companyName}.csv`;

        link.setAttribute("href", url);
        link.setAttribute("download", filename);
        link.style.visibility = "hidden";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        const message = companyId
          ? `CSV template downloaded for ${this.state.currentCompanyName}! Fill the required fields and import back.`
          : `CSV template downloaded! Fill the required fields and import back.`;

        this.notification.add(message, {
          title: "Template Downloaded",
          type: "success",
        });
      } else {
        throw new Error(result.error || "Failed to generate template");
      }
    } catch (error) {
      console.error(
        `Error downloading ${modelDisplayName} CSV template:`,
        error
      );
      this.notification.add(
        `Error downloading ${modelDisplayName} CSV template: ` + error.message,
        { title: "Download Error", type: "danger" }
      );
    }
  }

  // تحديث importCSV للتعامل مع company_id الاختياري
  async importCSV(model, modelDisplayName, companyField = "company_id") {
    const companyId = this.state.currentCompanyId;

    if (companyField && companyId) {
      console.warn(
        `No company selected for ${modelDisplayName} import, proceeding without company filter.`
      );
    }

    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".csv";

    input.onchange = async (event) => {
      const file = event.target.files[0];
      if (!file) return;

      try {
        const text = await this.readFile(file);
        const importArgs = [model, text];
        if (companyId) {
          importArgs.push(companyId);
        } else {
          importArgs.push(null);
        }
        if (companyField) {
          importArgs.push(companyField);
        }

        const result = await this.orm.call(
          "csv.handler",
          "import_csv_with_validation",
          importArgs
        );

        if (result.success) {
          let message = `Successfully imported ${result.total_created} ${modelDisplayName}!`;
          if (result.total_updated > 0) {
            message += ` Updated ${result.total_updated} existing records.`;
          }

          if (result.total_errors > 0) {
            // Extract row numbers from errors
            const errorRows = result.errors
              .map((error) => error.match(/Row (\d+)/)?.[1])
              .filter((row) => row)
              .map(Number);
            const uniqueErrorRows = [...new Set(errorRows)]; // Remove duplicates
            const errorRowsStr =
              uniqueErrorRows.length > 0
                ? `Errors occurred in rows: ${uniqueErrorRows.join(", ")}.`
                : "Errors occurred in some rows.";

            message += ` ${result.total_errors} records had errors. ${errorRowsStr}`;
            console.warn(
              `${modelDisplayName} import errors in rows:`,
              uniqueErrorRows
            );
            console.warn("Detailed errors:", result.errors);

            // Show first 3 errors in notification with row numbers
            if (result.errors && result.errors.length > 0) {
              const firstErrors = result.errors.slice(0, 3).join("\n");
              this.notification.add(
                `${message}\n\nFirst errors:\n${firstErrors}`,
                { title: "Partial Import Success", type: "warning" }
              );
            } else {
              this.notification.add(message, {
                title: "Partial Import Success",
                type: "warning",
              });
            }
          } else {
            this.notification.add(message, {
              title: "Import Successful",
              type: "success",
            });
          }

          if (result.records_created && result.records_created.length > 0) {
            console.log(`Created ${modelDisplayName}:`, result.records_created);
          }

          if (result.records_updated && result.records_updated.length > 0) {
            console.log(`Updated ${modelDisplayName}:`, result.records_updated);
          }

          await this.checkAndInitialize();
        } else {
          throw new Error(result.error || "Import failed");
        }
      } catch (error) {
        console.error(`Error importing ${modelDisplayName} CSV file:`, error);
        this.notification.add(
          `Error importing ${modelDisplayName} CSV file: ${error.message}`,
          { title: "Import Error", type: "danger" }
        );
      }
    };

    input.click();
  }

  // Helper to read file
  readFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  }

  // Generic method for downloading template
  async downloadTemplateForStep(stepId) {
    const step = this.state.steps.find((s) => s.id === stepId);
    if (!step) return;

    let modelDisplayName, companyField;
    switch (step.model) {
      case "mc.education.stages":
        modelDisplayName = "Educational Stages";
        companyField = "company_id";
        break;
      case "education.class":
        modelDisplayName = "Grades";
        companyField = "school";
        break;
      case "education.class.division":
        modelDisplayName = "Class Divisions";
        companyField = "school_id";
        break;
      case "res.company":
        modelDisplayName = "Companies";
        companyField = null; // الشركات لا تحتاج company_field
        break;
      case "education.academic.year":
        modelDisplayName = "Academic Years";
        companyField = null; // إذا لم يكن لها company field
        break;
      case "mc.religion":
        modelDisplayName = "Religions";
        companyField = null; // إذا لم يكن لها company field
        break;
      case "student.ldap.directory":
        modelDisplayName = "LDAP Directory";
        companyField = null; // إذا لم يكن لها company field
        break;
      case "mc.rooms":
        modelDisplayName = "Rooms";
        companyField = "company_id"; // للـ mc.rooms
        break;
      case "education.division":
        modelDisplayName = "Divisions";
        companyField = "company_id"; // أو أي field مناسب
        break;
      case "education.application":
        modelDisplayName = "Applications for the admission";
        companyField = "company_id"; // أو أي field مناسب
        break;
      case "education.student":
        modelDisplayName = "Student Record";
        companyField = "company_id"; // أو أي field مناسب
        break;
      default:
        modelDisplayName = step.title;
        companyField = "company_id";
    }

    await this.downloadCSVTemplate(step.model, modelDisplayName);
  }

  // تحديث importCSVForStep للتعامل مع النماذج المختلفة
  async importCSVForStep(stepId) {
    const step = this.state.steps.find((s) => s.id === stepId);
    if (!step) return;

    let modelDisplayName, companyField;
    switch (step.model) {
      case "mc.education.stages":
        modelDisplayName = "Educational Stages";
        companyField = "company_id";
        break;
      case "education.class":
        modelDisplayName = "Grades";
        companyField = "school";
        break;
      case "education.class.division":
        modelDisplayName = "Class Divisions";
        companyField = "school";
        break;
      case "res.company":
        modelDisplayName = "Companies";
        companyField = null; // الشركات لا تحتاج company_field
        break;
      case "education.academic.year":
        modelDisplayName = "Academic Years";
        companyField = null; // إذا لم يكن لها company field
        break;
      case "mc.religion":
        modelDisplayName = "Religions";
        companyField = null; // إذا لم يكن لها company field
        break;
      case "student.ldap.directory":
        modelDisplayName = "LDAP Directory";
        companyField = null; // إذا لم يكن لها company field
        break;
      case "mc.rooms":
        modelDisplayName = "Rooms";
        companyField = "company_id"; // للـ mc.rooms
        break;
      case "education.division":
        modelDisplayName = "Divisions";
        companyField = "company_id"; // أو أي field مناسب
        break;
      case "education.application":
        modelDisplayName = "Applications for the admission";
        companyField = "company_id"; // أو أي field مناسب
        break;
      case "education.student":
        modelDisplayName = "Student Record";
        companyField = "company_id"; // أو أي field مناسب
      default:
        modelDisplayName = step.title;
        companyField = "company_id";
    }

    await this.importCSV(step.model, modelDisplayName, companyField);
  }

  // Switch company by user - هنا بقى اليوزر يقدر يغير الشركة
  async UserSelectCompany(companyId) {
    // تحديث معرف الشركة الحالية
    this.state.currentCompanyId = companyId;

    // تحديث اسم الشركة من الذاكرة المؤقتة
    this.state.currentCompanyName = this.state.companyNames[companyId] || "";

    // تغيير سياق الشركة فعلياً في النظام
    await this.switchCompanyTo(companyId);

    // إظهار رسالة النجاح
    this.notification.add(
      `Selected company: ${this.state.currentCompanyName}`,
      { title: "Company Selected", type: "success" }
    );

    // إعادة فحص حالة الإعداد للشركة الجديدة
    await this.checkAndInitialize();
  }

  // Switch company context
  async switchCompanyTo(companyId) {
    const currentCompanyId = this.companyService.currentCompany.id;
    if (currentCompanyId === companyId) {
      return;
    }
    const allowedCompanies = this.companyService.allowedCompanies;
    if (companyId in allowedCompanies) {
      await this.companyService.setCompanies([companyId], true);
      this.notification.add(
        `Switched to: ${allowedCompanies[companyId].name}`,
        { title: "Company Switched", type: "info" }
      );
    } else {
      this.notification.add(
        "Please make sure you have access to the company and try again.",
        { title: "Company Access", type: "warning" }
      );
    }
  }

  hideOnboardingSteps() {
    this.state.showOnboarding = false;
  }

  showOnboardingSteps() {
    this.state.showOnboarding = true;
  }

  resetForNewConfiguration() {
    // مش هنغير currentCompanyId هنا عشان دي الشركة الحالية
    this.state.steps[0].complete_state = false;
    this.state.steps[1].complete_state = false;
    this.state.steps[2].complete_state = false;
    this.state.steps[3].complete_state = false;
    this.state.steps[4].complete_state = false;
    this.state.steps[5].complete_state = false;
    this.state.steps[6].complete_state = false;
    this.state.showOnboarding = true;
    this.openCompanyForm();
  }

  isStepDisabled(stepId) {
    if (stepId === 1) return false;
    if (stepId === 2) {
      return !this.state.steps[0].complete_state;
    }
    if (stepId === 3) {
      return !this.state.steps[0].complete_state;
    }
    if (stepId === 4) {
      return !this.state.steps[0].complete_state;
    }
    if (stepId === 5) {
      return !this.state.steps[0].complete_state;
    }
    if (stepId === 6) {
      return !this.state.steps[0].complete_state;
    }
    if (stepId === 7) {
      return !this.state.steps[0].complete_state;
    }
    if (stepId === 8) {
      return !this.state.steps[0].complete_state;
    }
    if (stepId === 9) {
      return !this.state.steps[0].complete_state;
    }
    if (stepId === 10) {
      return !this.state.steps[0].complete_state;
    }
    if (stepId === 11) {
      return !this.state.steps[0].complete_state;
    }
    return true;
  }

  executeStepAction(step) {
    if (this.isStepDisabled(step.id)) {
      if (step.id === 2 || step.id === 3 || step.id === 4) {
        this.notification.add("Please add a company first before proceeding.", {
          title: "Add Company Required",
          type: "warning",
        });
      }
      return;
    }
    this[step.action]();
  }
}
