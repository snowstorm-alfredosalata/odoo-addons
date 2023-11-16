# RDS Moulding Technology S.p.A. Odoo Modules

This repository contains Odoo 13.0 modules for exclusive use of RDS Moulding Technology S.p.A.
All modules, except third party modules, are (c) of RDS Moulding Technology S.p.A.

## Module List
### cloud_base, cloud_base_documents, onedrive
**Third Party** Made by faOtools and bought from the odoo App Store. Refear to its app store page for documentation. https://apps.odoo.com/apps/modules/13.0/cloud_base/

### account_budget_partner
Simply adds a partner_id fields to crossovered.budget.lines for enabling partner-based budgeting.

### accounting_dffm 
Enables support for italian-style end-of-month payment terms computation.

### binary_image_modal
Extends binary_image widget to open a modal displaying full-screen size image on user click.

### hr_attendance_book
Adds tables and functionality to manage attendance and leaves tabulations. Features exporting attendance data in plaintext for import in the program GIS.

### hr_shifts
Adds an hr_shift table to manage working shifts. Shifts allow employee to switch time table on regular intervals, automatically.

### l10n_it_ddt
RDS implementation of DDTs.

### l10n_it_edi_revised
Standard odoo implementation of italian electronic invoice, with slight modifications to keep the format compliant with latest norms.

### mrp_bom_costing_no_batching
Removes unwanted behaviour in BoM costing.

### mrp_concurrent_productions 
Allows creation of non-nestable, non-recursive parent-children relationship between BoMs.
When a production order for a parent BoM is launched, additional orders for all other children BoMs are automatically launched. 
Children BoM can not have a routing. Instead, costs from the Parent order's workorder are split between the parent and all children.

### mrp_subcontracting_bom_costing 
Adds subcontracting prices to subcontracting BoMs price calculation.

### mrp_subcontracting_purchase_ux
Changes UI on purchase orders to manage subcontractive in a cleaner, more intuitive way.

### odoo_kontrol
Extends mrp.workcenter.productivity to better aggregate data and more easily manage production loss types.
Implements a non-tableted way to manage workorders.
Exposes certain web hooks for receiving data regarding workcenter productivity from external routines.

### product_customerinfo 
Allows adding customer specific product code and description on products. Partner-specific product code and description are then added to name_get based on context.

### rds_customizations_hr
Miscellaneous customization on HR (reports, exposed fields...)

### rds_customizations_mrp
Miscellaneous customization on MRP (reports, exposed fields...)

### sale_report_residuals
Adds quantity to deliver and amount to delvier on sale reports.

### sales_order_document_commitment_date
Adds commitment date on sale order report.

### stock_mts_mto_rule
OCA module for mixed MTS/MTO behaviour. Currently decommissioning.

### vanilla_fixes
Fixes certain standerd odoo glitches.

### visitor
Handles visitors. Decommissioning.

### workorder_replanner
Adds a wizard to reschedule all workorders on select workcenter automatically.

### zpl_labels_mgmt
Adds utilities and tables to manage ZPL reports and network-print from within Odoo.
