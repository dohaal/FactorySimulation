import csv
import random
import string
import os
from textual import on
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.containers import Container, Horizontal, VerticalScroll, Vertical, ScrollableContainer, HorizontalScroll, Grid
from textual.widget import AwaitMount, Widget
from textual.widgets import Button, Footer, Header, Static, DataTable, Select, Label, Rule, Tree, ContentSwitcher, Input, ProgressBar
from textual_plotext import PlotextPlot
from plotext import datetimes_to_string 
from datetime import date, timedelta
import math

def main():
    app = FactorySimulation()
    app.run()

class MainScreen(Static):
    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        with Container(id="main-grid"):
            with Container(id="nav-bars"):
                with Container(id="top-info"):
                    yield Static("Funds:", id="funds")
                    #yield Static("Steel:", id="steel")
                    #yield Static("Aluminum:", id="aluminum")
                    #yield Static("Plastic:", id="plastic")
                    #yield Static("Electronics:", id="electronics")
                    #yield Static("Idle Operators:", id="idle_operators")
                    with Container():
                        yield Static("Date:", id="date")
                        yield Static("Day:", id="day")
                        yield Static("Turn:", id="turn")
                with Container(classes="top-navbar"):
                    yield Button("Sales", id="sales")
                    yield Button("Production", id="production")
                    yield Button("Planning", id="planning")
                    yield Button("Logistics", id="logistics")
                    yield Button("Procurement", id="procurement")
                    
                    yield Rule(orientation="vertical", line_style="heavy")
                    #yield Button("R & D | Finance | HR", id="research")

                    yield Rule(orientation="vertical", line_style="heavy")
                    yield Rule(orientation="vertical", line_style="heavy")
                    yield Rule(orientation="vertical", line_style="heavy")
                    #yield Button("Save Game", id="save_game")
                    #yield Button("End Turn", id="end_turn")
                    yield Button("End Day", id="end_day")

class SalesScreenPlot(PlotextPlot):
    def __init__(self,id):
        super().__init__(id=id)
        self._title = "Some Title"
        self._data: list[float] = []
        self._time: list[int] = []
    def replot(self,dates, sale_prices) -> None:
        """Redraw the plot."""
        self.plt.clear_data()
        self.plt.plot(dates, sale_prices)
        self.refresh()

class SalesScreen(Static):
    def __init__(self, products, warehouse, customer_order_list, selling_dict, product_sale_price_past_list, 
                 funds, sales_modifiers_list, current_date, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.products = products
        self.warehouse = warehouse
        self.customer_order_list = customer_order_list
        self.selling_dict = selling_dict
        self.product_sale_price_past_list = product_sale_price_past_list
        self.funds = funds
        self.sales_modifiers_list = sales_modifiers_list
        self.current_date = current_date
            
    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        with Container(id="sales-grid"):
            with Container(id="left-pane"):
                yield Select(allow_blank=True, id="sales_select_product", prompt="Select Product", options=[("placeholder",1)])
                yield Button("Add", id="sales_add_to_selling")
                yield Button("Clear", id="sales_clear_selling")
                yield Static("Products added to the list will be sold at the end of the day.", id="sales_label_selling_list")
                yield DataTable(id="sales_sale_list")
            with VerticalScroll(id="middle"):
                yield Static("PRODUCT PRICE AND INVENTORY")
                yield DataTable(id="sales_price_inventory_table")
                yield Static("Production cost is calculated with the current material and operation costs. ")
                yield Static("CUSTOMER ORDER DATA")
                yield DataTable(id="sales_customer_order_table")
            with Vertical(id="top-bottom-right"):
                with VerticalScroll(id="top-right"):
                    yield Static("SALES DEPARTMENT PRICE EXPECTATIONS FOR THIS WEEK")
                    yield Static(id="sales_modifier")
                    yield Static(""" This is only an expectation for the current week. These expectations may or may not be realized. There is a higher probability that it will.""")
                with VerticalScroll(id="bottom-right"):
                    yield Static("PRODUCT PRICES (LAST 30 DAYS)")
                    yield SalesScreenPlot(id="sales_price_history")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        product_ids = [product.id for product in self.products]

        sales_left_pane_table = self.query("#sales_sale_list").first()
        select_product = self.query("#sales_select_product").first()
        
        if button_id == "sales_add_to_selling":
            sales_left_pane_table.clear()
            if not sales_left_pane_table.columns:
                sales_left_pane_table.add_column("ID")
                sales_left_pane_table.add_column("QUANTITY")

            if select_product.value != Select.BLANK:
                product_id = product_ids[select_product.value - 1]
                if self.warehouse.product_storage[product_id] > self.selling_dict[product_id]:
                    customer_order_quantity = [order[2] for order in self.customer_order_list if order[0] == product_id][0]
                    if  customer_order_quantity > self.selling_dict[product_id]:
                        self.selling_dict[product_id] += 1
                for i in range(len(self.selling_dict)):
                    if self.selling_dict[product_ids[i]] > 0:
                        sales_left_pane_table.add_row(product_ids[i], self.selling_dict[product_ids[i]])

        elif button_id == "sales_clear_selling":
            sales_left_pane_table.clear()
            for item in self.selling_dict:
                self.selling_dict[item] = 0

    def update(self, products, warehouse, selling_dict, customer_order_list, product_sale_price_past_list,
                funds, sales_modifiers_list, current_date):
        self.products = products
        self.warehouse = warehouse
        self.selling_dict = selling_dict
        self.customer_order_list = customer_order_list
        self.product_sale_price_past_list = product_sale_price_past_list
        self.funds = funds
        self.sales_modifiers_list = sales_modifiers_list
        self.current_date = current_date

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.title = str(event.value)

        product_ids = [product.id for product in self.products]
        selected_product = product_ids[event.value - 1]
        sale_prices = [product["sale_price"] for day in self.product_sale_price_past_list for product in day if product["id"] == selected_product]
        dates = datetimes_to_string([product["date"] for day in self.product_sale_price_past_list for product in day if product["id"] == selected_product])
        plt = self.query_one(SalesScreenPlot)
        plt.data = sale_prices
        plt.time = dates
        plt.replot(dates=dates, sale_prices=sale_prices)

class PlanningScreen(Static):
    def __init__(self, products, warehouse, customer_order_list, selling_dict, product_sale_price_past_list, 
                 funds, sales_modifiers_list, current_date, planning_dict, workorders, operations, workcenters, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.products = products
        self.warehouse = warehouse
        self.customer_order_list = customer_order_list
        self.selling_dict = selling_dict
        self.planning_dict = planning_dict
        self.product_sale_price_past_list = product_sale_price_past_list
        self.funds = funds
        self.sales_modifiers_list = sales_modifiers_list
        self.current_date = current_date
        self.workorders = workorders
        self.workcenters = workcenters
        self.operations = operations

    def compose(self) -> ComposeResult:
            """Called to add widgets to the app."""
            with Container(id="planning-grid"):
                with Container(id="plannig-left-pane"):
                    yield Select(allow_blank=True, id="planning_select_product", prompt="Select Product", options=[("placeholder",1)])
                    yield Button("Add", id="planning_add_to_workorder")
                    yield Button("Clear", id="planning_clear_workorder")
                    yield DataTable(id="planning_workorder_list")
                    yield Button("Create Workorder", id="planning_create_workorder")
                with VerticalScroll(id="planning-middle"):
                    with Horizontal(id="planning_contentswitch_buttons"):
                        yield Button("Bill of Materials", id="planning_product_info_contentswitch") 
                        yield Button("Production Types", id="planning_materials_info_contentswitch")
                    with ContentSwitcher(initial="planning_product_info_contentswitch"):
                        with VerticalScroll(id="planning_materials_info_contentswitch"):
                            yield Static("PRODUCTION TYPES")
                            yield DataTable(id="planning_materials_info_table")
                            yield Static("WORKCENTER LOADS")
                            yield DataTable(id="planning_workcenter_load_table")    
                        with VerticalScroll(id="planning_product_info_contentswitch"):
                            yield Static("GENERAL INFORMATION")
                            yield DataTable(id="planning_product_info_table")    
                            yield Rule()
                            yield Static("PRODUCT BILL OF MATERIALS")
                            yield DataTable(id="planning_bill_of_material_table", zebra_stripes = True)

                with VerticalScroll(id="planning-right"):
                    yield Static("PROJECTED COMPLETION OF THE PLAN")
                    with Horizontal(id="planning-right-select-delete"):
                        yield Select(allow_blank=True, id="planning_workorder_select", prompt="Select Workorder", options=[("placeholder",1)])
                        yield Button("Delete Workorder", id="planning_delete_workorder")
                    tree: Tree[dict] = Tree("Workorders", id="planning_workorder_tree")
                    tree.root.expand()
                    yield tree

    def on_mount(self) -> None:
        materials_datatable = self.query("#planning_materials_info_table").first()
        materials_datatable.clear()

        if not materials_datatable.columns:
            materials_datatable.add_column("PRODUCT")
            materials_datatable.add_column("PRODUCT TYPE")
            materials_datatable.add_column("MACHINING")
            materials_datatable.add_column("BENDING")
            materials_datatable.add_column("CASTING")
            materials_datatable.add_column("FORGING")
            materials_datatable.add_column("PAINTJOB")
            materials_datatable.add_column("WELDING")

        for product in self.products:
            machining_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Machining")
            bending_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Bending")
            casting_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Casting")
            forging_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Forging")
            paintjob_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Paintjob")
            welding_total = sum(part.operation_times[index] * product.part_amounts[part.id] for part in product.product_parts for index, opr in enumerate(part.operations) if opr == "Welding")   
            materials_datatable.add_row(product.id,product.product_type,machining_total,bending_total,casting_total,forging_total,paintjob_total,welding_total)

        workcenter_workload_datatable = self.query("#planning_workcenter_load_table").first()
        workcenter_workload_datatable.clear()

        if not workcenter_workload_datatable.columns:
            workcenter_workload_datatable.add_column("WORKCENTER TYPE")
            workcenter_workload_datatable.add_column("WORKCENTER WORKLOAD")
            workcenter_workload_datatable.add_column("WORKCENTER STATIONS")

        for workcenter in self.workcenters:
            if workcenter.prod_method != "Assembly":
                workcenter_type = workcenter.prod_method
                workcenter_workload = sum(operation.remaining_work for operation in workcenter.operations)
                workcenter_stations = workcenter.station_count
                workcenter_workload_datatable.add_row(workcenter_type, workcenter_workload, workcenter_stations)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        
        button_id = event.button.id
        product_ids = [product.id for product in self.products]

        planning_workorder_table = self.query("#planning_workorder_list").first()
        select_product = self.query("#planning_select_product").first()
        
        if button_id == "planning_add_to_workorder":
            planning_workorder_table.clear()
            if not planning_workorder_table.columns:
                planning_workorder_table.add_column("ID")
                planning_workorder_table.add_column("QUANTITY")

            if select_product.value != Select.BLANK:
                product_id = product_ids[select_product.value - 1]
                self.planning_dict[product_id] += 1
                for i in range(len(self.planning_dict)):
                    if self.planning_dict[product_ids[i]] > 0:
                        planning_workorder_table.add_row(product_ids[i], self.planning_dict[product_ids[i]])

        elif button_id == "planning_clear_workorder":
            planning_workorder_table.clear()
            for item in self.planning_dict:
                self.planning_dict[item] = 0
        
        elif button_id == "planning_create_workorder":
            planning_workorder_table = self.query("#planning_workorder_list").first()
            
            new_workorder = WorkOrder(loaded_products=self.planning_dict,workorders=self.workorders,current_date=self.current_date,
                                      operations=self.operations,products=self.products,workcenters=self.workcenters,
                                      warehouse=self.warehouse)
            self.workorders.append(new_workorder)
            handle_planning_button(self)
            self.query("#planning_workorder_tree").first().refresh()

            planning_workorder_table.clear()
            for item in self.planning_dict:
                self.planning_dict[item] = 0
        
        elif button_id == "planning_delete_workorder":
            planning_workorder_select = self.query("#planning_workorder_select").first()
            current_workorder = self.workorders[planning_workorder_select.value - 1] 
            for workcenter in self.workcenters:
                flag = True
                while flag:
                    flag = False
                    for index, operation in enumerate(workcenter.operations):
                        if operation.workorder_id == current_workorder.id:
                            workcenter.operations.pop(index)
                            flag = True

            self.workorders.pop(planning_workorder_select.value - 1)
            handle_planning_button(self)
            self.query("#planning_workorder_tree").first().refresh()
        else:
            self.query_one(ContentSwitcher).current = event.button.id

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        select_id = event.select.id
        if select_id == "planning_select_product":
            self.title = str(event.value)
            product_ids = [product.id for product in self.products]
            selected_product = product_ids[event.value - 1]

            product = [product for product in self.products if product.id == selected_product][0]

            bill_of_material_table = self.query("#planning_bill_of_material_table").first()
            bill_of_material_table.clear()
            for index, part in enumerate(product.product_parts):
                bill_of_material_table.add_row(index+1, part.id, part.name, product.part_amounts[part.id], f"{part.assembly_time} turns", part.raw_material_name, f"{part.raw_material.cost} $",
                                                f"{part.lead_time} turns", part.operations, f"{part.operation_times} turns")
                
            planning_product_info_table = self.query("#planning_product_info_table").first()
            planning_product_info_table.clear()
            
            planning_product_info_table.add_row("PRODUCT ID", product.id)
            planning_product_info_table.add_row("PRODUCT TYPE", product.product_type)
            planning_product_info_table.add_row("DISTINCT PART COUNT", product.part_count)
            planning_product_info_table.add_row("PRODUCTION COST", f"{product.production_cost} $")
            planning_product_info_table.add_row("PRODUCTION TIME", f"{product.total_manufacturing_time} turns")
            planning_product_info_table.add_row("MAIN WORK TYPE", f"{product.production_type_leaning}")
            planning_product_info_table.add_row("ASSEMBLY TIME", f"{product.total_assembly_time} turns")

class ProductionScreen(Static):
    def __init__(self, products, warehouse, workorders, workcenters, raw_materials, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.products = products
        self.warehouse = warehouse
        self.workorders = workorders
        self.workcenters = workcenters
        self.raw_materials = raw_materials
        self.active_workcenter_text = ""

    def compose(self) -> ComposeResult:
        with Container(id="planning-grid"):
            with ScrollableContainer(id="production-left-pane"):
                yield Static("WORKCENTERS")
            with ScrollableContainer(id="production-right-pane"):
                with Horizontal():
                    yield Select(allow_blank=True, id="production-select-opr", prompt="Select Operation", options=[("placeholder",1)])
                    yield Button("Increase", id="production-increase-que")
                    yield Button("Decrease", id="production-decrease-que")
                yield Static("DETAILS")
                yield DataTable(id="production-raw-materials-datatable")
                yield DataTable(id="production-total-work")
                yield DataTable(id="production-datatable")
    
    def on_mount(self) -> None:
        production_datatable = self.query("#production-datatable").first()
        production_datatable.clear()

        columns = []
        for column in production_datatable.columns:
            columns.append(column)
        for column in columns:
            production_datatable.remove_column(column)

        if not production_datatable.columns:
            production_datatable.add_column("NO")
            production_datatable.add_column("OPERATION ID")
            production_datatable.add_column("PRODUCT ID")
            production_datatable.add_column("PART ID")
            production_datatable.add_column("WORKORDER ID")
            production_datatable.add_column("TASK")
            production_datatable.add_column("UNFINISHED STOCK")
            production_datatable.add_column("NEEDED AMOUNT")
            production_datatable.add_column("REMAINING WORK")
        
        production_datatable_totalwork = self.query("#production-total-work").first()
        production_datatable_totalwork.clear()
        if not production_datatable_totalwork.columns:
            production_datatable_totalwork.add_column("WORKCENTER ID")
            production_datatable_totalwork.add_column("TOTAL WORK")

    def on_button_pressed(self, event: Button.Pressed) -> None:
            """Event handler called when a button is pressed."""
            button_id = event.button.id
            if "start" in button_id:
                button_id = button_id[6:]
            elif "stop" in button_id:
                 button_id = button_id[5:]

            production_datatable = self.query("#production-datatable").first()
            production_datatable_totalwork = self.query("#production-total-work").first()
            production_select_opr = self.query("#production-select-opr").first()

            self.active_workcenter_text = "ASS"

            for index, workcenter in enumerate(self.workcenters):
                if button_id == f"{workcenter.id}" and "ASS" not in f"{workcenter.id}":
                    self.active_workcenter_text = button_id
                    production_datatable.clear()
                    production_datatable_totalwork.clear()
                    for i in range(len(self.workcenters)):
                        self.query(f"#{self.workcenters[i].id}-1").first().remove_class("production-add-border")
                    self.query(f"#{button_id}-1").first().add_class("production-add-border")

                    columns = []
                    for column in production_datatable_totalwork.columns:
                        columns.append(column)
                    for column in columns:
                        production_datatable_totalwork.remove_column(column)

                    current_operations_total_work = sum(operation.remaining_work for workcenter in self.workcenters for operation in workcenter.operations if workcenter.id == button_id)
                    if not production_datatable_totalwork.columns:
                        production_datatable_totalwork.add_column("WORKCENTER ID")
                        production_datatable_totalwork.add_column("TOTAL WORK")
                    production_datatable_totalwork.add_row(workcenter.id, current_operations_total_work)

                    columns = []
                    for column in production_datatable.columns:
                        columns.append(column)
                    for column in columns:
                        production_datatable.remove_column(column)

                    if not production_datatable.columns:
                        production_datatable.add_column("NO")
                        production_datatable.add_column("OPERATION ID")
                        production_datatable.add_column("PRODUCT ID")
                        production_datatable.add_column("PART ID")
                        production_datatable.add_column("WORKORDER ID")
                        production_datatable.add_column("TASK")
                        production_datatable.add_column("UNFINISHED STOCK")
                        production_datatable.add_column("NEEDED AMOUNT")
                        production_datatable.add_column("REMAINING WORK")
                    for index2, operation in enumerate(workcenter.operations):
                        workorder = [workorder for workorder in self.workorders if workorder.id == operation.workorder_id][0]
                        is_product_of_workorder_finished = workorder.finished[operation.product_id]
                        if not is_product_of_workorder_finished: 
                            unfinished_part_stock = self.warehouse.check_unfinished_part_stocks(operation.loaded_part.id)
                            production_datatable.add_row(index2+1, operation.id, operation.product_id, operation.loaded_part.id, operation.workorder_id, operation.task, unfinished_part_stock,
                                                      (operation.part_amount * operation.product_amount), f"{operation.remaining_work} turns") 
                    opr_list = []
                    for operation in workcenter.operations:
                        opr_list.append((operation.id, operation.id))
                    production_select_opr.set_options(opr_list)
                elif "ASS" in button_id:
                    self.active_workcenter_text = button_id
                    production_datatable.clear()
                    production_datatable_totalwork.clear()

                    columns = []
                    for column in production_datatable_totalwork.columns:
                        columns.append(column)
                    for column in columns:
                        production_datatable_totalwork.remove_column(column)

                    if not production_datatable_totalwork.columns:
                        production_datatable_totalwork.add_column("NO")
                        production_datatable_totalwork.add_column("PRODUCT ID")
                        production_datatable_totalwork.add_column("PRODUCT COUNT")
                        production_datatable_totalwork.add_column("WORKORDER ID")
                        production_datatable_totalwork.add_column("ALL PARTS READY")

                    for workorder in self.workorders:
                        for index, product_text in enumerate(workorder.loaded_products):
                            if workorder.loaded_products[product_text] != 0:
                                product = [product for product in self.products if product.id == product_text][0]
                                are_all_parts_available = product.check_stock_for_assembly(self.warehouse, workorder.loaded_products[product_text], workorder)
                                production_datatable_totalwork.add_row(index+1, product_text, workorder.loaded_products[product_text], workorder.id, are_all_parts_available)
   
                    columns = []
                    for column in production_datatable.columns:
                        columns.append(column)
                    for column in columns:
                        production_datatable.remove_column(column)

                    if not production_datatable.columns:
                        production_datatable.add_column("NO")
                        production_datatable.add_column("OPERATION ID")
                        production_datatable.add_column("PRODUCT ID")
                        production_datatable.add_column("PART ID")
                        production_datatable.add_column("WORKORDER ID")
                        production_datatable.add_column("TASK")
                        production_datatable.add_column("FINISHED STOCK")
                        production_datatable.add_column("NEEDED AMOUNT")
                        production_datatable.add_column("REMAINING WORK")
                    for index2, operation in enumerate(workcenter.operations):
                        workorder = [workorder for workorder in self.workorders if workorder.id == operation.workorder_id][0]
                        is_product_of_workorder_finished = workorder.finished[operation.product_id]
                        if not is_product_of_workorder_finished: 
                            finished_part_stock = self.warehouse.check_finished_part_stocks(operation.loaded_part.id)
                            production_datatable.add_row(index2+1, operation.id, operation.product_id, operation.loaded_part.id, operation.workorder_id, operation.task, finished_part_stock,
                                                      (operation.part_amount * operation.product_amount), f"{operation.remaining_work} turns") 

            if button_id == "production-increase-que":
                if "ASS" not in f"{self.active_workcenter_text}":
                    workcenter = [workcenter for workcenter in self.workcenters if workcenter.id == self.active_workcenter_text][0]
                    if production_select_opr.value != Select.BLANK:
                        for index, operation in enumerate(workcenter.operations):
                            if operation.id == production_select_opr.value:
                                popped_opr = workcenter.operations.pop(index)
                                workcenter.operations.insert(index-1, popped_opr)
                        production_datatable.clear()
                    if not production_datatable.columns:
                        production_datatable.add_column("NO")
                        production_datatable.add_column("OPERATION ID")
                        production_datatable.add_column("PRODUCT ID")
                        production_datatable.add_column("PART ID")
                        production_datatable.add_column("WORKORDER ID")
                        production_datatable.add_column("TASK")
                        production_datatable.add_column("UNFINISHED STOCK")
                        production_datatable.add_column("NEEDED AMOUNT")
                        production_datatable.add_column("REMAINING WORK")
                    for index2, operation in enumerate(workcenter.operations):
                        workorder = [workorder for workorder in self.workorders if workorder.id == operation.workorder_id][0]
                        is_product_of_workorder_finished = workorder.finished[operation.product_id]
                        if not is_product_of_workorder_finished: 
                            unfinished_part_stock = self.warehouse.check_unfinished_part_stocks(operation.loaded_part.id)
                            production_datatable.add_row(index2+1, operation.id, operation.product_id, operation.loaded_part.id, operation.workorder_id, operation.task, unfinished_part_stock,
                                                      (operation.part_amount * operation.product_amount), f"{operation.remaining_work} turns") 
            elif button_id == "production-decrease-que":
                if "ASS" not in f"{self.active_workcenter_text}":
                    workcenter = [workcenter for workcenter in self.workcenters if workcenter.id == self.active_workcenter_text][0]
                    if production_select_opr.value != Select.BLANK:
                        for index, operation in enumerate(workcenter.operations):
                            if operation.id == production_select_opr.value:
                                popped_opr = workcenter.operations.pop(index)
                                workcenter.operations.insert(index+1, popped_opr)
                                break
                        production_datatable.clear()
                    if not production_datatable.columns:
                        production_datatable.add_column("NO")
                        production_datatable.add_column("OPERATION ID")
                        production_datatable.add_column("PRODUCT ID")
                        production_datatable.add_column("PART ID")
                        production_datatable.add_column("WORKORDER ID")
                        production_datatable.add_column("TASK")
                        production_datatable.add_column("UNFINISHED STOCK")
                        production_datatable.add_column("NEEDED AMOUNT")
                        production_datatable.add_column("REMAINING WORK")
                    for index2, operation in enumerate(workcenter.operations):
                        workorder = [workorder for workorder in self.workorders if workorder.id == operation.workorder_id][0]
                        is_product_of_workorder_finished = workorder.finished[operation.product_id]
                        if not is_product_of_workorder_finished: 
                            unfinished_part_stock = self.warehouse.check_unfinished_part_stocks(operation.loaded_part.id)
                            production_datatable.add_row(index2+1, operation.id, operation.product_id, operation.loaded_part.id, operation.workorder_id, operation.task, unfinished_part_stock,
                                                      (operation.part_amount * operation.product_amount), f"{operation.remaining_work} turns") 

class ProductionWidget(Static):
    def __init__(self, workcenter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workcenter = workcenter
        if self.workcenter.active == False:
            self.main_color = "warning"
            self.start_button_status = "success"
        else:
            self.main_color = "success"
            self.start_button_status = "error"

    def on_mount(self) -> None:
        if self.workcenter.active == False:
            self.query(f"#start-{self.workcenter.id}").first().remove_class("production-passive")
            self.query(f"#start-{self.workcenter.id}").first().add_class("production-active")
            self.query(f"#stop-{self.workcenter.id}").first().add_class("production-passive")
            self.query(f"#stop-{self.workcenter.id}").first().remove_class("production-active")
        else:
            self.query(f"#start-{self.workcenter.id}").first().add_class("production-passive")
            self.query(f"#start-{self.workcenter.id}").first().remove_class("production-active")
            self.query(f"#stop-{self.workcenter.id}").first().remove_class("production-passive")
            self.query(f"#stop-{self.workcenter.id}").first().add_class("production-active")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if "start" in button_id:
            if len(self.workcenter.operations) > 0:
                self.add_class("production-active-passive")
                self.query(f"#{self.workcenter.id}").first().variant = "success"
                self.workcenter.active = True
                self.query("#production_active_status").first().update(f"ACTIVE: {self.workcenter.active}")

                self.query(f"#start-{self.workcenter.id}").first().add_class("production-passive")
                self.query(f"#start-{self.workcenter.id}").first().remove_class("production-active")
                self.query(f"#stop-{self.workcenter.id}").first().remove_class("production-passive")
                self.query(f"#stop-{self.workcenter.id}").first().add_class("production-active")
            elif "ASS" in self.workcenter.id:
                if len(self.workcenter.operations) > 0:
                    self.add_class("production-active-passive")
                    self.query(f"#{self.workcenter.id}").first().variant = "success"
                    self.workcenter.active = True
                    self.query("#production_active_status").first().update(f"ACTIVE: {self.workcenter.active}")

                    self.query(f"#start-{self.workcenter.id}").first().add_class("production-passive")
                    self.query(f"#start-{self.workcenter.id}").first().remove_class("production-active")
                    self.query(f"#stop-{self.workcenter.id}").first().remove_class("production-passive")
                    self.query(f"#stop-{self.workcenter.id}").first().add_class("production-active")                
                
        elif "stop" in  button_id:
            self.remove_class("production-active-passive")
            self.query(f"#{self.workcenter.id}").first().variant = "warning"
            self.workcenter.active = False
            self.query("#production_active_status").first().update(f"ACTIVE: {self.workcenter.active}")
            #self.query(f"#{self.workcenter.id}").first().press()

            self.query(f"#start-{self.workcenter.id}").first().remove_class("production-passive")
            self.query(f"#start-{self.workcenter.id}").first().add_class("production-active")
            self.query(f"#stop-{self.workcenter.id}").first().add_class("production-passive")
            self.query(f"#stop-{self.workcenter.id}").first().remove_class("production-active")

    def compose(self) -> ComposeResult:
        with Button(id=f"{self.workcenter.id}", variant=f"{self.main_color}"):
            with Horizontal(id="production-widget"):
                yield Button("Start", id=f"start-{self.workcenter.id}", variant=f"primary", classes="production-start-stop-margin")
                yield Button("Stop", id=f"stop-{self.workcenter.id}", variant="error", classes="production-start-stop-margin")
                with Vertical(classes="production_widget_info"):
                    yield Static(f"ID: {self.workcenter.id}")
                    yield Static(f"PROD METHOD: {self.workcenter.prod_method}")
                    yield Static(f"ACTIVE: {self.workcenter.active}", id="production_active_status")
                with Vertical():
                    yield Static(f"OPR COST: {self.workcenter.operating_cost}")
                    yield Static(f"OPERATORS: {self.workcenter.operator_count}")
                    yield Static(f"STATIONS: {self.workcenter.station_count}")
                with Vertical():
                    if len(self.workcenter.operations) > 0:
                        yield Static(f"OPERATION: {self.workcenter.operations[0].id}")
                        yield Static(f"REMAINING WORK: {self.workcenter.operations[0].remaining_work} turns")
                        yield Static(f"WORKORDER: {self.workcenter.operations[0].workorder_id}")
                    else:
                        yield Static(f"OPERATION: None")
                        yield Static(f"REMAINING WORK: None")
                        yield Static(f"WORKORDER: None")

class ProcurementScreen(Static):
    def __init__(self, products, warehouse, workorders, workcenters, raw_materials, current_date,
                 raw_material_cost_past_list, app, procurement_modifiers_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.products = products
        self.warehouse = warehouse
        self.workorders = workorders
        self.workcenters = workcenters
        self.raw_materials = raw_materials
        self.raw_material_cost_past_list = raw_material_cost_past_list
        self.current_date = current_date
        self.procurement_modifiers_list = procurement_modifiers_list

    def compose(self) -> ComposeResult:
        with Container(id="planning-grid"):
            with ScrollableContainer(id="procurement-left-pane"):
                yield Static("RAW MATERIALS")
            with VerticalScroll(id="procurement-right-pane"):
                with Container():
                    with Horizontal(id="planning_contentswitch_buttons"):
                        yield Button("Market Expectations", id="procurement_expectations_info_contentswitch") 
                        yield Button("Current Stocks", id="procurement_materials_stock_contentswitch")
                    with ContentSwitcher(initial="procurement_expectations_info_contentswitch"):
                        with VerticalScroll(id="procurement_expectations_info_contentswitch"):
                            yield Static("PROCUREMENT DEPARTMENT COST EXPECTATIONS")
                            yield Static(id="procurement_modifier")
                            yield Static(""" This is only an expectation for the current week. These expectations may or may not be realized. There is a higher probability that it will.""")
                        with VerticalScroll(id="procurement_materials_stock_contentswitch"):
                            yield Static("CURRENT STOCKS")
                            with Horizontal(id="procurement-selects"):
                                yield Select(allow_blank=True, id="procurement_select_workorder", prompt="Select Workorder", options=[("placeholder",1)])
                                yield Select(allow_blank=True, id="procurement_select_product", prompt="Select Product", options=[("placeholder",1)])
                            yield DataTable(id="procurement_materials_stock_table")
                with Container():
                    yield Static("MATERIAL COST FOR THE LAST 30 DAYS")
                    yield ProcurementScreenPlot(name="procurement_cost_history")

    def update(self, products, warehouse, workorders, workcenters, raw_materials,
                raw_material_cost_past_list, procurement_modifiers_list, current_date):
        self.products = products
        self.warehouse = warehouse
        self.workorders = workorders
        self.workcenters = workcenters
        self.raw_materials = raw_materials
        self.raw_material_cost_past_list = raw_material_cost_past_list
        self.procurement_modifiers_list = procurement_modifiers_list
        self.current_date = current_date

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        buy_button_ids = [f"{material.code}-buy-button" for material in self.raw_materials]
        raw_material_codes = [raw_material.code for raw_material in self.raw_materials]
        if button_id in raw_material_codes:
            selected_material = button_id
            raw_material_costs = [raw_material["cost"] for day in self.raw_material_cost_past_list for raw_material in day if raw_material["code"] == selected_material]
            dates = datetimes_to_string([raw_material["date"] for day in self.raw_material_cost_past_list for raw_material in day if raw_material["code"] == selected_material])

            plt = self.query_one(ProcurementScreenPlot)
            plt.data = raw_material_costs
            plt.time = dates
            plt.replot(dates=dates, costs=raw_material_costs)
        elif button_id in buy_button_ids:
            pass
        else:
            self.query_one(ContentSwitcher).current = event.button.id
    def on_mount(self) -> None:
        pass

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.title = str(event.value)
        select_id = event.select.id

        if select_id == "procurement_select_workorder":
            if event.value != Select.BLANK:
                selected_workorder = [workorder for workorder in self.workorders if workorder.id == event.value][0]
                procurement_select_product = self.query("#procurement_select_product").first()
                product_select_options = []

                loaded_product_ids = [product for product in selected_workorder.loaded_products if selected_workorder.loaded_products[product] != 0]
                for i in range(len(loaded_product_ids)):
                    product_select_options.append((loaded_product_ids[i], loaded_product_ids[i]))
                procurement_select_product.set_options(product_select_options)

        if select_id == "procurement_select_product":
            selected_product_id = event.value
            if selected_product_id != Select.BLANK:
                selected_workorder_text = self.query("#procurement_select_workorder").first().value
                if selected_workorder_text != Select.BLANK:
                    selected_workorder = [workorder for workorder in self.workorders if workorder.id == selected_workorder_text][0]
                    selected_product = [product for product in self.products if product.id == selected_product_id][0]
                    procurement_materials_stock_table = self.app.procurement_screen.query("#procurement_materials_stock_table").first()
                    procurement_materials_stock_table.clear()
                    if not procurement_materials_stock_table.columns:
                        procurement_materials_stock_table.add_column("ID")
                        procurement_materials_stock_table.add_column("MATERIAL NAME")
                        procurement_materials_stock_table.add_column("STOCKS")
                        procurement_materials_stock_table.add_column("EXPENDITURE")
                    
                    material_need_all = selected_product.calculate_raw_material_need(selected_workorder)
                    for material in self.app.procurement_screen.raw_materials:
                        material_need = material_need_all[material.code]
                        procurement_materials_stock_table.add_row(material.code, material.name, self.warehouse.raw_material_stocks[material.code],
                                                                 material_need)

class ProcurementWidget(Static):
    def __init__(self, raw_material, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raw_material = raw_material

    @on(Input.Changed)
    def select_changed(self, event: Input.Changed) -> None:
        input_id = event.input.id
        total_cost_id_list = input_id.split("-")
        total_cost_id = f"{total_cost_id_list[0]}-total-cost"

        total_cost_static = self.query(f"#{total_cost_id}").first()
        input_quan = self.query(f"#{input_id}").first()
        if input_quan.value != "":
            total_cost_static.update(renderable=f"TOTAL COST: { int(input_quan.value) * int(self.raw_material.cost)}")
        else:
            total_cost_static.update(renderable=f"TOTAL COST: {0}")
    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == f"{self.raw_material.code}-buy-button":

            input_value = self.query(f"#{self.raw_material.code}-input").first().value
            if input_value == "":
                input_value = 0
            if self.raw_material.minimum_order_quantity <= int(input_value):
                self.app.push_screen(ProcurementBuyScreen(input_value, self.raw_material))
            else:
                self.app.push_screen(ProcurementWarningScreen())

    def compose(self) -> ComposeResult:
        with Button(id=f"{self.raw_material.code}"):
            with Horizontal(id="procurement-widget"):
                yield Button("Buy", id=f"{self.raw_material.code}-buy-button", variant=f"primary", classes="procurement_start_stop_margin")
                yield Input(placeholder="An integer", type="integer", classes="procurement_input", id=f"{self.raw_material.code}-input")
                with Vertical(classes="procurement_input"):
                    yield Static(f"RAW MATERIAL:{self.raw_material.name}")
                    yield Static(f"TOTAL COST: {0}", id=f"{self.raw_material.code}-total-cost")
                with Vertical(classes="procurement_input"):
                    yield Static(f"UNIT COST: {self.raw_material.cost}")
                    yield Static(f"MIN ORDER QNT: {self.raw_material.minimum_order_quantity}", id=f"{self.raw_material.code}-order-quan")
                    #yield Static(f"LEAD TIME: {self.raw_material.lead_time}")

class ProcurementScreenPlot(PlotextPlot):
    def __init__(self,name):
        super().__init__(name=name)
        self._title = "Some Title"
        self._data: list[float] = []
        self._time: list[int] = []
    def replot(self,dates, costs) -> None:
        """Redraw the plot."""
        self.plt.clear_data()
        self.plt.plot(dates, costs)
        self.refresh()

class ProcurementBuyScreen(ModalScreen[bool]):
    """Screen with a dialog to quit."""
    def __init__ (self, input_value, raw_material, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quantity = int(input_value)
        self.raw_material = raw_material

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to buy?", id="question"),
            Button("Buy", variant="primary", id="buy"),
            Button("Cancel", variant="default", id="cancel"),
            id="dialog",
        )
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "buy":
            total_price = self.quantity * self.raw_material.cost
            if total_price < self.app.funds:
                self.app.funds = self.app.funds - total_price
                funds_static = self.app.main_screen.query("#funds").first()
                funds_static.update(renderable=f"Funds: {self.app.funds}")                 
                self.app.warehouse.raw_material_stocks[self.raw_material.code] += self.quantity

                procurement_materials_stock_table = self.app.procurement_screen.query("#procurement_materials_stock_table").first()
                procurement_materials_stock_table.clear()
                if not procurement_materials_stock_table.columns:
                    procurement_materials_stock_table.add_column("ID")
                    procurement_materials_stock_table.add_column("MATERIAL NAME")
                    procurement_materials_stock_table.add_column("STOCKS")
                    procurement_materials_stock_table.add_column("EXPENDITURE")
                for material in self.app.procurement_screen.raw_materials:
                    procurement_materials_stock_table.add_row(material.code, material.name, self.app.warehouse.raw_material_stocks[material.code],"-") 
                self.dismiss(True)
            else:
                self.dismiss(False)
            #self.dismiss(True)
        else:
            self.dismiss(False)

class ProcurementWarningScreen(ModalScreen[bool]):
    """Screen with a dialog to quit."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Please type an amount larger than the minimum order quantity.", id="question-2"),
            Button("Cancel", variant="default", id="cancel2"),
            id="dialog-2",
        )
    def on_button_pressed(self, event: Button.Pressed) -> None:
            self.dismiss(False)

class LogisticsScreen(Static):
    def __init__(self, products, warehouse, customer_order_list, selling_dict, product_sale_price_past_list, 
                 funds, sales_modifiers_list, current_date, planning_dict, workorders, operations, workcenters,
                  raw_materials, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.products = products
        self.warehouse = warehouse
        self.customer_order_list = customer_order_list
        self.selling_dict = selling_dict
        self.planning_dict = planning_dict
        self.product_sale_price_past_list = product_sale_price_past_list
        self.funds = funds
        self.sales_modifiers_list = sales_modifiers_list
        self.current_date = current_date
        self.workorders = workorders
        self.workcenters = workcenters
        self.operations = operations
        self.raw_materials = raw_materials

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        with Container(id="planning-grid"):
            with ScrollableContainer(id="logistics-left-pane"):
                yield Static("WAREHOUSE SHELVES", classes="center-mid")
                yield Button("Buy New Shelf", variant=f"primary", classes="center-mid", id="logistics_buy_shelf")
            with VerticalScroll(id="logistics-mid-pane"):
                yield Static("WAREHOUSE INFO")
                yield DataTable(id="logistics_table")
            with VerticalScroll(id="logistics-right-pane"):
                yield Static("CURRENT RAW MATERIAL STOCKS")
                yield Select(allow_blank=True, id="logistics_select_workorder", prompt="Select Workorder", options=[("placeholder",1)])
                yield Select(allow_blank=True, id="logistics_select_product", prompt="Select Product", options=[("placeholder",1)])
                yield Button("Transfer Material", variant=f"primary", id="logistics_transfer_raw_material")
                yield DataTable(id="logistics_materials_stock_table")

    def on_mount(self) -> None:
        logistics_table = self.app.logistics_screen.query("#logistics_table").first()
        logistics_table.clear()
        if not logistics_table.columns:
            logistics_table.add_column("SHELF")
            logistics_table.add_column("ADDRESS")
            logistics_table.add_column("PART CODE")
            logistics_table.add_column("PART NAME")
            logistics_table.add_column("UNFINISHED")
            logistics_table.add_column("BEING WORKED")
            logistics_table.add_column("FINISHED")
        shelf = self.warehouse.shelves[0]
        for address in shelf.addresses:
            logistics_table.add_row(shelf.code, address, shelf.addresses[address], shelf.partnames[address], shelf.unfinished_part_stocks[address], shelf.being_worked_on[address], shelf.finished_part_stocks[address])

        logistics_materials_stock_table = self.app.logistics_screen.query("#logistics_materials_stock_table").first()
        logistics_materials_stock_table.clear()
        if not logistics_materials_stock_table.columns:
            logistics_materials_stock_table.add_column("ID")
            logistics_materials_stock_table.add_column("MATERIAL NAME")
            logistics_materials_stock_table.add_column("STOCKS")
            logistics_materials_stock_table.add_column("EXPENDITURE")
            logistics_materials_stock_table.add_column("TRANSFER STATUS")
        for material in self.app.logistics_screen.raw_materials:
            logistics_materials_stock_table.add_row(material.code, material.name, self.warehouse.raw_material_stocks[material.code],
                                                     "-", False) 

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        shelve_codes = [shelf.code for shelf in self.warehouse.shelves]
        button_id = event.button.id
        if button_id == "logistics_buy_shelf":
            self.app.push_screen(LogisticsBuyShelfScreen(warehouse=self.warehouse))
        elif button_id == "logistics_transfer_raw_material":
            
            selected_workorder_text = self.query("#logistics_select_workorder").first().value
            selected_workorder = [workorder for workorder in self.workorders if workorder.id == selected_workorder_text][0]
            selected_product_text = self.query("#logistics_select_product").first().value
            selected_product = [product for product in self.products if product.id == selected_product_text][0]
            if selected_product != "":    
                material_need_all = selected_product.calculate_raw_material_need(selected_workorder)
                flag = True
                for material in self.app.logistics_screen.raw_materials:
                    material_need = material_need_all[material.code]
                    material_stock = self.warehouse.raw_material_stocks[material.code]
                    if material_need > material_stock:
                        flag = False
                        break
                if flag == True:
                    for material in self.app.logistics_screen.raw_materials:
                        material_need = material_need_all[material.code]
                        material_stock = self.warehouse.raw_material_stocks[material.code]
                        self.warehouse.raw_material_stocks[material.code] = self.warehouse.raw_material_stocks[material.code] - material_need
                    self.workorders
                    for part in selected_product.product_parts:
                        for shelf in self.warehouse.shelves:
                            for address in shelf.addresses:
                                if shelf.addresses[address] == part.id:
                                    if part.raw_material.code != "E1":
                                        shelf.unfinished_part_stocks[address] += (selected_workorder.loaded_products[selected_product.id] * selected_product.part_amounts[part.id])
                                    else:
                                        shelf.finished_part_stocks[address] += (selected_workorder.loaded_products[selected_product.id] * selected_product.part_amounts[part.id])
                                        
                    logistics_table = self.app.logistics_screen.query("#logistics_table").first()
                    logistics_table.clear()
                    if not logistics_table.columns:
                        logistics_table.add_column("SHELF")
                        logistics_table.add_column("ADDRESS")
                        logistics_table.add_column("PART CODE")
                        logistics_table.add_column("PART NAME")
                        logistics_table.add_column("UNFINISHED")
                        logistics_table.add_column("BEING WORKED")
                        logistics_table.add_column("FINISHED")
                    shelf = self.warehouse.shelves[0]
                    for address in shelf.addresses:
                        logistics_table.add_row(shelf.code, address, shelf.addresses[address], shelf.partnames[address], shelf.unfinished_part_stocks[address], shelf.being_worked_on[address], shelf.finished_part_stocks[address])
                    
                    logistics_materials_stock_table = self.app.logistics_screen.query("#logistics_materials_stock_table").first()
                    logistics_materials_stock_table.clear()
                    if not logistics_materials_stock_table.columns:
                        logistics_materials_stock_table.add_column("ID")
                        logistics_materials_stock_table.add_column("MATERIAL NAME")
                        logistics_materials_stock_table.add_column("STOCKS")
                        logistics_materials_stock_table.add_column("EXPENDITURE")
                        logistics_materials_stock_table.add_column("TRANSFER STATUS")
                    selected_workorder.loaded_products_transfer_status[selected_product.id] = True
                    for material in self.app.logistics_screen.raw_materials:
                        logistics_materials_stock_table.add_row(material.code, material.name, self.warehouse.raw_material_stocks[material.code], 
                                                                "-", selected_workorder.loaded_products_transfer_status[selected_product.id]) 
        elif button_id in shelve_codes:    
            logistics_table = self.app.logistics_screen.query("#logistics_table").first()
            logistics_table.clear()
            if not logistics_table.columns:
                logistics_table.add_column("SHELF")
                logistics_table.add_column("ADDRESS")
                logistics_table.add_column("PART CODE")
                logistics_table.add_column("PART NAME")
                logistics_table.add_column("UNFINISHED")
                logistics_table.add_column("BEING WORKED")
                logistics_table.add_column("FINISHED")
            shelf = [shelf for shelf in self.warehouse.shelves if shelf.code == button_id][0]
            for address in shelf.addresses:
                logistics_table.add_row(shelf.code, address, shelf.addresses[address], shelf.partnames[address], shelf.unfinished_part_stocks[address], shelf.being_worked_on[address], shelf.finished_part_stocks[address]) 

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.title = str(event.value)
        select_id = event.select.id

        if select_id == "logistics_select_workorder":
            if event.value != Select.BLANK:
                selected_workorder = [workorder for workorder in self.workorders if workorder.id == event.value][0]
                logistics_select_product = self.query("#logistics_select_product").first()
                product_select_options = []

                loaded_product_ids = [product for product in selected_workorder.loaded_products if selected_workorder.loaded_products[product] != 0]
                for i in range(len(loaded_product_ids)):
                    product_select_options.append((loaded_product_ids[i], loaded_product_ids[i]))
                logistics_select_product.set_options(product_select_options)

        if select_id == "logistics_select_product":
            selected_product_id = event.value
            if selected_product_id != Select.BLANK:
                selected_workorder_text = self.query("#logistics_select_workorder").first().value
                if selected_workorder_text != Select.BLANK:
                    selected_workorder = [workorder for workorder in self.workorders if workorder.id == selected_workorder_text][0]
                    selected_product = [product for product in self.products if product.id == selected_product_id][0]
                    logistics_materials_stock_table = self.app.logistics_screen.query("#logistics_materials_stock_table").first()
                    logistics_materials_stock_table.clear()
                    if not logistics_materials_stock_table.columns:
                        logistics_materials_stock_table.add_column("ID")
                        logistics_materials_stock_table.add_column("MATERIAL NAME")
                        logistics_materials_stock_table.add_column("STOCKS")
                        logistics_materials_stock_table.add_column("EXPENDITURE")
                        logistics_materials_stock_table.add_column("TRANSFER STATUS")
                    
                    material_need_all = selected_product.calculate_raw_material_need(selected_workorder)
                    for material in self.app.logistics_screen.raw_materials:
                        material_need = material_need_all[material.code]
                        logistics_materials_stock_table.add_row(material.code, material.name, self.warehouse.raw_material_stocks[material.code],
                                                                 material_need, selected_workorder.loaded_products_transfer_status[selected_product.id])

class LogisticsWidget(Static):
    def __init__(self, shelve, logistics_screen, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shelve = shelve

    def on_mount(self) -> None:
        counter = 0
        for address in self.shelve.addresses:
            if self.shelve.addresses[address] != "":    
                counter += 1
        self.query_one(ProgressBar).advance(counter)
        self.query("#percentage").first().update(f"STORAGE CAPACITY: {counter} / 100")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

    def compose(self) -> ComposeResult:
        with Button(id=f"{self.shelve.code}"):
            with Horizontal():
                with Vertical(classes="logistics_container"):
                    yield Static(f"SHELF NUMBER:{self.shelve.code}")
                    yield Static("STORAGE CAPACITY:", id=f"percentage")
                    yield ProgressBar(total=100, show_eta=False, id=f"{self.shelve.code}-progress")  

class LogisticsBuyShelfScreen(ModalScreen[bool]):
    """Screen with a dialog to quit."""
    def __init__ (self, warehouse, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warehouse = warehouse

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("A new shelf costs 10000$. Are you sure you want to buy?", id="question"),
            Button("Buy", variant="primary", id="buy"),
            Button("Cancel", variant="default", id="cancel"),
            id="dialog",
        )
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "buy":
            SHELF_PRICE = 10000
            
            for index, shelve in enumerate(self.app.logistics_screen.warehouse.shelves):
                self.app.logistics_screen.query(LogisticsWidget).first().remove()
            new_shelf = self.warehouse.add_shelf()
            for index, shelve in enumerate(self.app.logistics_screen.warehouse.shelves):
                new_logistics_widget = LogisticsWidget(shelve=shelve, logistics_screen=self.app.logistics_screen, id=f"{shelve.code}-shelve")
                self.app.logistics_screen.query("#logistics-left-pane").first().mount(new_logistics_widget)
            self.app.funds -= SHELF_PRICE
            funds_static = self.app.main_screen.query("#funds").first()
            funds_static.update(renderable=f"Funds: {self.app.funds}")  

            self.dismiss(True)
        else:
            self.dismiss(False)

class FactorySimulation(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.products = []
        self.workcenters = []
        self.workorders = []
        self.operations = [] #so that we can check if the created ids are unique
        self.selling_dict = {}
        self.planning_dict = {}
        self.customer_order_list = []
        self.warehouse = None
        self.part_name_data = None
        self.raw_materials = None
        self.production_methods = None
        self.sales_modifiers_list = []
        self.procurement_modifiers_list = []
        self.current_date = date(year=2024, month=1, day=1)
        self.product_sale_price_past_list = []
        self.raw_material_cost_past_list = []
        self.funds = 50000
        self.days_of_the_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.raw_materials_dict = {}
        self.raw_material_mapping = {}

        self.active_workcenter_text = ""
        
        self.sales_screen = None
        self.planning_screen = None
        self.procurement_screen = None
        self.logistics_screen = None
        self.main_screen = None
        self.production_screen = None
    CSS = """ 
        #main_screen {
            height: 22%;
        }
      
        #main-grid {
            layout: grid;
            grid-size: 12;
        }
        #sales-grid {
            layout: grid;
            grid-size: 12;
        }
        #left-pane > * {
            color: auto;
            padding: 1;
            align: center middle;
        }
        #left-pane > Button {
            width: 80%;
            height: 3;
            padding: 0;
            margin-top: 1;
            margin-left: 5;
            margin-right: 4;
        }
        #sales_label_selling_list {
            margin-top: 1;
        }
        #sales_sale_list {
            margin-top: 2;
            height: 20%;
        }
        #left-pane {
            height: 100%;
            background: $panel;
            border: white;
            column-span: 2;
        }
        #top-bottom-right{
            column-span:4;
            margin: 0;
            height: 100%;
        }
        #top-right {
            height: 50%;
            background: $panel;
            border: white;
        }
        #top-right > Static {
            margin-bottom: 1;
            margin-right: 1;
            background: $boost;
        }
        #bottom-right {
            background: $panel;
            border: white;
        }
        #bottom-right > Static {
            background: $boost;
        }
        #top-info {
            layout: grid;
            grid-size: 7;
            dock: top;
            width: 100%;
            height: 5;
            background: $panel;
            column-span: 5;
        }
        #top-info > Static {
            background: $boost;
            color: auto;
            padding: 2;
        }
        .top-navbar {
            layout: horizontal;
            column-span: 5;
            background: $panel;
            border-top: white;

        }
        .top-navbar > Button {
            background: $boost;
            color: auto;
            text-align: center;
            align: left middle;
            margin-left: 3;
            border: white;
            height: 100%;
        }
        .top-navbar > Button :hover {
            border: gray;
        }
        #middle {
            column-span: 6;
            background: $boost;
            border: white;
        }
        #middle > Static {
            text-align: center;
            text-style: bold;
        }
        #sales_price_inventory_table {
            height: 50%;
        }
        #nav-bars {
            column-span: 12;
            margin: 0;
            border: white;
        }
        #planning-grid {
            layout: grid;
            grid-size: 12;
        }
        #plannig-left-pane {
            height: 100%;
            background: $panel;
            border: white;
            column-span: 2;
        }
        #plannig-left-pane > Button {
            width: 80%;
            height: 3;
            padding: 0;
            margin-top: 1;
            margin-left: 5;
            margin-right: 4;
        }
        #plannig-left-pane > * {
            color: auto;
            padding: 1;
            align: center middle;
        }
        #planning-middle {
            column-span: 6;
            background: $boost;
            border: white;
        }
        #planning-right {
            column-span: 6;
            background: $boost;
            border: white;
        }
        #planning-right-select-delete {
            height: 15%;
            margin-top: 1;
        }
        #planning_contentswitch_buttons {
            height: 3;
            width: 40%;
        }   
        ProductionWidget {
            layout: horizontal;
            background: $boost;
            height: 5;
            margin: 1;
            min-width: 50;
        }
        #start {
            dock: left;
            margin-left: 1;
        }
        #stop {
            dock: left;
            display: none;
            margin-left: 1;
        }
        #production-left-pane {
            height: 100%;
            background: $panel;
            border: white;
            column-span: 6;
        }
        #production-right-pane {
            height: 100%;
            background: $panel;
            border: white;
            column-span: 6;
        }
        #production-right-pane > Horizontal {
            max-height: 4;
            min-height: 3;
            margin: 2;
            max-width: 70;
        }
        #production-decrease-que {
            margin-left: 2;
        }
        #production-increase-que {
            margin-left: 2;
        }
        #production-select-opr {
            max-width: 50;
        }
        .production_widget_info{
            margin-left: 2;
        }
        #production-left-pane > ProductionWidget{
            padding: 0;
            margin: 1;
            background: $boost;
        }
        .production-passive {
            display: none; 
        }
        .production-active {
            display: block;
        }
        .production-add-border {
            border-left:  red;
            padding: 0;
        }
        .production-start-stop-margin {
            margin-left: 2;
        }
        #procurement-right-pane {
            height: 100%;
            background: $panel;
            border: white;
            column-span: 6;
        }
        #procurement-left-pane {
            height: 100%;
            background: $panel;
            border: white;
            column-span: 6;
        }
        #procurement-left-pane > ProcurementWidget{
            padding: 0;
            margin: 1;
            background: $boost;
        }
        ProcurementWidget {
            layout: horizontal;
            background: $boost;
            height: 5;
            margin: 1;
            min-width: 50;
            padding: 1;
        }
        .procurement_input {
            width: 25%;
            margin-left: 2;
        }
        .procurement_start_stop_margin {
            margin-left: 2;
        }
        .procurement-add-border {
            border-left:  white;
            padding: 0;
        }

        ProcurementBuyScreen {
            align: center middle;
         }

        ProcurementWarningScreen {
            align: center middle;
         }

        #procurement-selects {
            margin-top: 1;
            max-height: 4;
            min-height: 3;
        }
         
        #dialog {
            grid-size: 2;
            grid-gutter: 1 2;
            grid-rows: 1fr 3;
            padding: 0 1;
            width: 60;
            height: 11;
            border: thick $background 80%;
            background: $surface;
        }

        #dialog-2 {
            grid-size: 2;
            grid-gutter: 1 2;
            grid-rows: 1fr 3;
            padding: 0 1;
            width: 60;
            height: 11;
            border: thick $background 80%;
            background: $warning;
        }
        #question {
            column-span: 2;
            height: 1fr;
            width: 1fr;
            content-align: center middle;
        }
        #question-2 {
            column-span: 2;
            height: 1fr;
            width: 1fr;
            content-align: center middle;
            color: black;
        }
        Grid > Button {
            width: 100%;
        }
        #logistics-mid-pane {
            height: 100%;
            background: $panel;
            border: white;
            column-span: 6;
            align: center middle;
        }
        #logistics-left-pane {
            height: 100%;
            background: $panel;
            border: white;
            column-span: 3;
        }
        #logistics-right-pane {
            height: 100%;
            background: $panel;
            border: white;
            column-span: 3;
        }
        #logistics-right-pane > * {
            margin-bottom: 2;
            margin-left: 2;
            margin-right: 2;
            align: center middle;
            text-align: center;
        }
        #logistics-right-pane > Button {
            width: 100%;
            margin-top: 1;
            margin-bottom: 2;
            margin-left: 5;
            margin-right: 5;
        }
        #logistics-left-pane > * {
            align: center middle;
            text-align: center;
        }
        #logistics-left-pane > Button {
            width: 100%;
            margin-top: 1;
            margin-left: 5;
            margin-right: 5;
        }
        #logistics-left-pane > LogisticsWidget{
            padding: 0;
            margin: 1;
            background: $boost;
        }
        LogisticsWidget {
            layout: horizontal;
            background: $boost;
            height: 5;
            margin: 1;
            padding: 1;
        }
        Bar > .bar--indeterminate {
            color: $primary;
            background: $secondary;
        }

        Bar > .bar--bar {
            color: $success;
            background: $primary 30%;
        }

        Bar > .bar--complete {
            color: $error;
        }
        PercentageStatus {
            text-style: reverse;
            color: $secondary;
        }
        .logistics_container {
            width: 100%;
            margin-left: 2;
        }
      LogisticsBuyShelfScreen {
            align: center middle;
         }
     """

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        with Vertical():
            yield MainScreen(id="main_screen")
            yield Container(id="sub_screen")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id

        if button_id == "sales":
            if self.query(SalesScreen):
                self.query(SalesScreen).last().remove()
            if self.query(PlanningScreen):
                self.query(PlanningScreen).last().remove()
            if self.query(ProductionScreen):
                self.query(ProductionScreen).last().remove()
            if self.query(ProcurementScreen):
                self.query(ProcurementScreen).last().remove()
            if self.query(LogisticsScreen):
                self.query(LogisticsScreen).last().remove()
            self.sales_screen = SalesScreen(products=self.products, warehouse=self.warehouse, 
                            selling_dict=self.selling_dict, customer_order_list=self.customer_order_list, 
                            product_sale_price_past_list=self.product_sale_price_past_list, funds=self.funds, 
                            sales_modifiers_list=self.sales_modifiers_list, current_date=self.current_date,
                            id="sales_screen")
            await self.query_one("#sub_screen").mount(self.sales_screen)
            handle_sales_button(self.sales_screen, self)

        elif button_id == "planning":
            if self.query(SalesScreen):
                self.query(SalesScreen).last().remove()
            if self.query(PlanningScreen):
                self.query(PlanningScreen).last().remove()
            if self.query(ProductionScreen):
                self.query(ProductionScreen).last().remove()
            if self.query(ProcurementScreen):
                self.query(ProcurementScreen).last().remove()
            if self.query(LogisticsScreen):
                self.query(LogisticsScreen).last().remove()
            self.planning_screen = PlanningScreen(products=self.products, warehouse=self.warehouse, 
                            selling_dict=self.selling_dict, customer_order_list=self.customer_order_list, 
                            product_sale_price_past_list=self.product_sale_price_past_list, funds=self.funds, 
                            sales_modifiers_list=self.sales_modifiers_list, current_date=self.current_date,
                            planning_dict=self.planning_dict, workorders=self.workorders, operations=self.operations,
                            workcenters=self.workcenters, id="planning_screen")
            await self.query_one("#sub_screen").mount(self.planning_screen)
            handle_planning_button(self.planning_screen)

        elif button_id == "production":
            if self.query(SalesScreen):
                self.query(SalesScreen).last().remove()
            if self.query(PlanningScreen):
                self.query(PlanningScreen).last().remove()
            if self.query(ProductionScreen):
                self.query(ProductionScreen).last().remove()
            if self.query(ProcurementScreen):
                self.query(ProcurementScreen).last().remove()
            if self.query(LogisticsScreen):
                self.query(LogisticsScreen).last().remove()
            self.production_screen = ProductionScreen(products=self.products, warehouse=self.warehouse,
                                                      workorders=self.workorders, workcenters=self.workcenters,
                                                      raw_materials=self.raw_materials, id="production_screen")
            await self.query_one("#sub_screen").mount(self.production_screen)
            handle_production_button(self.production_screen, self)
            
        elif button_id == "procurement":
            if self.query(SalesScreen):
                self.query(SalesScreen).last().remove()
            if self.query(PlanningScreen):
                self.query(PlanningScreen).last().remove()
            if self.query(ProductionScreen):
                self.query(ProductionScreen).last().remove()
            if self.query(ProcurementScreen):
                self.query(ProcurementScreen).last().remove()
            if self.query(LogisticsScreen):
                self.query(LogisticsScreen).last().remove()
            self.procurement_screen = ProcurementScreen(products=self.products, warehouse=self.warehouse,
                                                      workorders=self.workorders, workcenters=self.workcenters,
                                                      raw_materials = self.raw_materials, app=self, current_date=self.current_date,
                                                      raw_material_cost_past_list=self.raw_material_cost_past_list,
                                                      procurement_modifiers_list=self.procurement_modifiers_list,
                                                      id="procurement_screen")
            await self.query_one("#sub_screen").mount(self.procurement_screen)
            handle_procurement_button(self.procurement_screen, self)
        elif button_id == "logistics":
            if self.query(SalesScreen):
                self.query(SalesScreen).last().remove()
            if self.query(PlanningScreen):
                self.query(PlanningScreen).last().remove()
            if self.query(ProductionScreen):
                self.query(ProductionScreen).last().remove()
            if self.query(ProcurementScreen):
                self.query(ProcurementScreen).last().remove()
            if self.query(LogisticsScreen):
                self.query(LogisticsScreen).last().remove()
            self.logistics_screen = LogisticsScreen(products=self.products, warehouse=self.warehouse, 
                            selling_dict=self.selling_dict, customer_order_list=self.customer_order_list, 
                            product_sale_price_past_list=self.product_sale_price_past_list, funds=self.funds, 
                            sales_modifiers_list=self.sales_modifiers_list, current_date=self.current_date,
                            planning_dict=self.planning_dict, workorders=self.workorders, operations=self.operations,
                            workcenters=self.workcenters, raw_materials=self.raw_materials, id="logistics_screen")
            await self.query_one("#sub_screen").mount(self.logistics_screen)
            handle_logistics_button(self.logistics_screen)
        elif button_id == "end_turn":
            pass
        elif button_id == "end_day":
            
            handle_endday_button(app=self, selling_dict=self.selling_dict, products=self.products, 
                                 workcenters=self.workcenters, warehouse=self.warehouse, 
                                 customer_order_list=self.customer_order_list, raw_materials=self.raw_materials,
                                 workorders=self.workorders)

            sub_screen = self.query_one("#sub_screen")

    def on_mount(self) -> None:
        self.bind("q", "quit", description="Quit")

        self.part_name_data = part_names_csv_reader()
        self.production_methods = ['Machining', 'Bending', 'Casting', 'Forging', 'Paintjob', 'Welding']
        self.warehouse = Warehouse()
        self.raw_materials = initial_raw_material_generation(self)
        self.workcenters = initial_workcenter_data_generation(warehouse=self.warehouse, workcenters=self.workcenters, production_methods=self.production_methods,
                                                                workorders=self.workorders, products=self.products)
        self.products = initial_machine_data_generation(lg=3, md=3, sm=3,warehouse=self.warehouse, products=self.products, workorders=self.workorders, 
                                                production_methods=self.production_methods, raw_materials=self.raw_materials,
                                                part_name_data=self.part_name_data, workcenters=self.workcenters, selling_dict=self.selling_dict,
                                                planning_dict=self.planning_dict, raw_material_mapping=self.raw_material_mapping,
                                                raw_materials_dict=self.raw_materials_dict)
        self.workcenters.append(Assembly(warehouse=self.warehouse, workcenters=self.workcenters, workorders=self.workorders,
                                            products=self.products))
        self.customer_order_list = generate_customer_order_data(self.products, self.workcenters)

        self.product_sale_price_past_list = initial_product_price_history_generation(products=self.products, workcenters=self.workcenters, current_date=self.current_date)
        self.raw_material_cost_past_list = initial_raw_material_cost_history_generation(raw_materials=self.raw_materials, current_date=self.current_date)

        self.sales_modifiers_list = generate_sale_modifier(products=self.products, workcenters=self.workcenters)
        self.procurement_modifiers_list = generate_procurement_modifier(raw_materials=self.raw_materials)

        self.main_screen = self.query("#main_screen").first()

        idle_operators = 3
        funds_static = self.query("#funds").first()
        funds_static.renderable = f"funds: {self.funds}"

        date_static = self.query("#date").first()
        date_static.renderable = f"Date: {self.current_date}"

        day_static = self.query("#day").first()
        day_static.renderable = f"Date: {self.days_of_the_week[self.current_date.weekday()]}"

def handle_sales_button(sales_screen, app):
    sales_screen.update(products=app.products, warehouse=app.warehouse, customer_order_list=app.customer_order_list, 
                    selling_dict=app.selling_dict, product_sale_price_past_list=app.product_sale_price_past_list,
                    funds=app.funds, sales_modifiers_list=app.sales_modifiers_list, current_date=app.current_date)
    
    upper_middle_table = sales_screen.query("#sales_price_inventory_table").first()
    lower_middle_table = sales_screen.query("#sales_customer_order_table").first()
    upper_right_modifier_static = sales_screen.query("#sales_modifier").first()

    upper_middle_table.clear()
    lower_middle_table.clear()

    modifier_string = ""
    for modifier in sales_screen.sales_modifiers_list:
        if "decrease" in modifier['text']:
            color = "[red]"
        elif "increase" in modifier['text']:
            color = "[bold green]"
        modifier_string += f"{color}{modifier['text']} in price for {modifier['type']}[/]\n"
    upper_right_modifier_static.update(modifier_string)
    sales_screen.refresh()

    #past sales price generation is done for 29 days after that todays info is added here
    if len(sales_screen.product_sale_price_past_list) < 30:
        current_day_product_sale_price_list = [{'id': product.id, 'sale_price': product.sale_price, 'date': sales_screen.current_date} for product in sales_screen.products]
        sales_screen.product_sale_price_past_list.append(current_day_product_sale_price_list)

    sales_select_product = app.query("#sales_select_product")
    if len(sales_select_product.nodes) > 0:
        if sales_select_product.first().value != Select.BLANK:
            sales_select_field_index = sales_select_product.first().value - 1
            selected_product = app.products[sales_select_field_index].id
        else:
            selected_product = app.products[0].id

    sale_prices = [product["sale_price"] for day in sales_screen.product_sale_price_past_list for product in day if product["id"] == selected_product]
    dates = datetimes_to_string([product["date"] for day in sales_screen.product_sale_price_past_list for product in day if product["id"] == selected_product])

    plt = sales_screen.query_one(SalesScreenPlot)
    plt.data = sale_prices
    plt.time = dates
    plt.replot(dates=dates, sale_prices=sale_prices)

    sales_select_product = sales_screen.query("#sales_select_product").first()
    product_select_options_just_text = [product.id for product in sales_screen.products]
    product_select_options = []
    for i in range(len(sales_screen.products)):
        product_select_options.append((product_select_options_just_text[i],i+1))
    sales_select_product.set_options(product_select_options)

    if not upper_middle_table.columns:
        upper_middle_table.add_column("ID")
        upper_middle_table.add_column("PRODUCT TYPE")
        upper_middle_table.add_column("SALE PRICE")
        upper_middle_table.add_column("PRODUCTION COST")
        upper_middle_table.add_column("PROFITIT/LOSS")
        upper_middle_table.add_column("INVENTORY")
    for product in sales_screen.products:
        upper_middle_table.add_row(product.id, product.product_type, product.sale_price, product.production_cost, product.exchange, sales_screen.warehouse.product_storage[product.id])

    if not lower_middle_table.columns:
        lower_middle_table.add_column("ID")
        lower_middle_table.add_column("PRODUCT TYPE")
        lower_middle_table.add_column("QUANTITIY")
    for order in sales_screen.customer_order_list:
        lower_middle_table.add_row(order[0], order[1], order[2])

def handle_planning_button(self):
    planning_select_product = self.query("#planning_select_product").first()
    planning_select_options_just_text = [product.id for product in self.products]
    planning_select_options = []
    for i in range(len(self.products)):
        planning_select_options.append((planning_select_options_just_text[i],i+1))
    planning_select_product.set_options(planning_select_options)

    product = self.products[0]

    bill_of_material_table = self.query("#planning_bill_of_material_table").first()
    bill_of_material_table.clear()
    if not bill_of_material_table.columns:
        bill_of_material_table.add_column("NO")
        bill_of_material_table.add_column("PART ID")
        bill_of_material_table.add_column("PART NAME")
        bill_of_material_table.add_column("AMOUNT")
        bill_of_material_table.add_column("ASSEMBLY TIME")
        bill_of_material_table.add_column("RAW MATERIAL")
        bill_of_material_table.add_column("RM COST")
        bill_of_material_table.add_column("LEAD TIME")
        bill_of_material_table.add_column("OPERATIONS")
        bill_of_material_table.add_column("OPERATION TIMES")
    for index, part in enumerate(product.product_parts):
        bill_of_material_table.add_row(index+1, part.id, part.name, product.part_amounts[part.id], f"{part.assembly_time} turns", part.raw_material_name, f"{part.raw_material.cost} $", f"{part.lead_time} turns", part.operations, f"{part.operation_times} turns")

    planning_product_info_table = self.query("#planning_product_info_table").first()
    planning_product_info_table.clear()
    if not planning_product_info_table.columns:
        planning_product_info_table.add_column("CATEGORY")
        planning_product_info_table.add_column("VALUE")
    
        planning_product_info_table.add_row("PRODUCT ID", product.id)
        planning_product_info_table.add_row("PRODUCT TYPE", product.product_type)
        planning_product_info_table.add_row("DISTINCT PART COUNT", product.part_count)
        planning_product_info_table.add_row("PRODUCTION COST", f"{product.production_cost} $")
        planning_product_info_table.add_row("PRODUCTION TIME", f"{product.total_manufacturing_time} turns")
        planning_product_info_table.add_row("MAIN WORK TYPE", f"{product.production_type_leaning}")
        planning_product_info_table.add_row("ASSEMBLY TIME", f"{product.total_assembly_time} turns")

    tree = self.query("#planning_workorder_tree").first()
    tree.clear()
    planning_select_delete_workorder = self.query("#planning_workorder_select").first()
    planning_select_delete_workorder_options = []
    for index, workorder in enumerate(self.workorders):
        planning_select_delete_workorder_options.append((workorder.id, index+1))
        workorder_root = tree.root.add(f"{workorder.id}", expand=True)
        workorder_root.add_leaf(f"PRODUCTS: {workorder.loaded_products}")
        workorder_root.add_leaf(f"START DATE: {workorder.date}")
        workorder_root.add_leaf(f"FINISHED: {workorder.finished}")
        
        workorder_operations = workorder_root.add(f"Manufacturing Operations")
        for operation in workorder.wo_operations:
            individual_operation = workorder_operations.add(f"{operation.id}")
            individual_operation.add_leaf(f"PART ID: {operation.loaded_part.id}")
            individual_operation.add_leaf(f"TASK: {operation.task}")
            individual_operation.add_leaf(f"RAW MATERIAL: {operation.raw_material}")
            individual_operation.add_leaf(f"PART AMOUNT: {operation.part_amount}")
            individual_operation.add_leaf(f"PRODUCT AMOUNT: {operation.product_amount}")
            individual_operation.add_leaf(f"REMAININT WORK: {operation.remaining_work}")

        workorder_assembly_operations = workorder_root.add(f"Assembly Operations")
        for operation in workorder.wo_assembly_operations:
            individual_operation = workorder_assembly_operations.add(f"{operation.id}")
            individual_operation.add_leaf(f"PART ID: {operation.loaded_part.id}")
            individual_operation.add_leaf(f"TASK: {operation.task}")
            individual_operation.add_leaf(f"PART AMOUNT: {operation.part_amount}")
            individual_operation.add_leaf(f"PRODUCT AMOUNT: {operation.product_amount}")
            individual_operation.add_leaf(f"REMAININT WORK: {operation.remaining_work}")
    
    planning_select_delete_workorder.set_options(planning_select_delete_workorder_options)

def handle_production_button(self, app):
    for index, workcenter in enumerate(self.workcenters):
        new_production_widget = ProductionWidget(workcenter=workcenter, id=f"{workcenter.id}-1")
        self.query("#production-left-pane").first().mount(new_production_widget)

def handle_logistics_button(logistics_screen):
    for index, shelve in enumerate(logistics_screen.warehouse.shelves):
        new_logistics_widget = LogisticsWidget(shelve=shelve, logistics_screen=logistics_screen, id=f"{shelve.code}-shelve")
        logistics_screen.query("#logistics-left-pane").first().mount(new_logistics_widget)
        #new_logistics_widget.query_one(ProgressBar).advance(counter)
        #logistics_screen.query(f"#{shelve_code}-progress").first().advance(counter)

    logistics_select_workorder = logistics_screen.query("#logistics_select_workorder").first()
    workorder_ids = [workorder.id for workorder in logistics_screen.workorders]
    workorder_select_options = []
    for i in range(len(logistics_screen.workorders)):
        workorder_select_options.append((workorder_ids[i], workorder_ids[i]))
    logistics_select_workorder.set_options(workorder_select_options)

def handle_procurement_button(procurement_screen, app):
    procurement_screen.update(products=app.products, warehouse=app.warehouse, workorders=app.workorders,
                                workcenters=app.workcenters,raw_materials=app.raw_materials,
                                raw_material_cost_past_list=app.raw_material_cost_past_list,
                                procurement_modifiers_list = app.procurement_modifiers_list,
                                current_date=app.current_date)
    
    for index, raw_material in enumerate(procurement_screen.raw_materials):
        new_procurement_widget = ProcurementWidget(raw_material=raw_material, app=procurement_screen, id=f"{raw_material.code}")
        procurement_screen.query("#procurement-left-pane").first().mount(new_procurement_widget)

    upper_right_modifier_static = procurement_screen.query("#procurement_modifier").first()
    modifier_string = ""
    for modifier in procurement_screen.procurement_modifiers_list:
        if "decrease" in modifier['text']:
            color = "[red]"
        elif "increase" in modifier['text']:
            color = "[bold green]"
        modifier_string += f"{color}{modifier['text']} in price for {modifier['type']}[/]\n"
    upper_right_modifier_static.update(modifier_string)
    procurement_screen.refresh()

    #past sales price generation is done for 29 days after that todays info is added here
    if len(procurement_screen.raw_material_cost_past_list) < 30:
        current_day_raw_material_cost_list = [{'code': raw_material.code, 'cost': raw_material.cost, 'date': procurement_screen.current_date} for raw_material in procurement_screen.raw_materials]
        procurement_screen.raw_material_cost_past_list.append(current_day_raw_material_cost_list)

    selected_material = procurement_screen.raw_materials[0].code
    raw_material_costs = [raw_material["cost"] for day in procurement_screen.raw_material_cost_past_list for raw_material in day if raw_material["code"] == selected_material]
    dates = datetimes_to_string([raw_material["date"] for day in procurement_screen.raw_material_cost_past_list for raw_material in day if raw_material["code"] == selected_material])

    plt = procurement_screen.query_one(ProcurementScreenPlot)
    plt.data = raw_material_costs
    plt.time = dates
    plt.replot(dates=dates, costs=raw_material_costs)

    selected_workorder_text = procurement_screen.query("#procurement_select_workorder").first().value

    procurement_materials_stock_table = procurement_screen.query("#procurement_materials_stock_table").first()
    if not procurement_materials_stock_table.columns:
        procurement_materials_stock_table.add_column("ID")
        procurement_materials_stock_table.add_column("MATERIAL NAME")
        procurement_materials_stock_table.add_column("STOCKS")
        procurement_materials_stock_table.add_column("EXPENDITURE")
    for material in procurement_screen.raw_materials:
        procurement_materials_stock_table.add_row(material.code, material.name, app.warehouse.raw_material_stocks[material.code],"-")

    procurement_select_workorder = procurement_screen.query("#procurement_select_workorder").first()
    workorder_ids = [workorder.id for workorder in procurement_screen.workorders]
    workorder_select_options = []
    for i in range(len(procurement_screen.workorders)):
        workorder_select_options.append((workorder_ids[i], workorder_ids[i]))
    procurement_select_workorder.set_options(workorder_select_options)

def handle_endday_button(app, selling_dict, products, warehouse, customer_order_list, workcenters,
                          raw_materials, workorders):
    total_funds_gained = 0
    return_dict = {}

    #<---------------SALES---------------->
    #calculates the total funds gained by selling the products in the selling dict
    for item in selling_dict:
        for product in products:
            if item == product.id:
                for product_id in warehouse.product_storage:
                    if item == product_id:
                        warehouse.product_storage[item] -= selling_dict[item]
                total_funds_gained += product.sale_price * selling_dict[item]

    new_generated_list = generate_sale_modifier(products=products, workcenters=workcenters)
    app.sales_modifiers_list.clear()
    for item in new_generated_list:
        app.sales_modifiers_list.append(item)

    new_customer_order_list = generate_customer_order_data(products=products, workcenters=workcenters) 
    app.customer_order_list.clear()
    for item in new_customer_order_list:
        app.customer_order_list.append(item)

    return_dict["funds"] = int(total_funds_gained)

    #adds the calculated gained funds to he existing funds
    funds_static = app.query("#funds").first()
    app.funds += total_funds_gained
    funds_static.update(renderable=f"Funds: {app.funds}")

    #updates the date
    app.current_date += timedelta(days=1)
    date_static = app.query("#date").first()
    date_static.update(renderable = f"Date: {app.current_date}")
    day_static = app.query("#day").first()
    day_static.update(renderable = f"Day: {app.days_of_the_week[app.current_date.weekday()]}")

    #updates the product prices
    current_day_product_sale_price_list = [{'id': product.id, 'sale_price': product.sale_price, 'date': app.current_date} for product in app.products]
    app.product_sale_price_past_list.append(current_day_product_sale_price_list)
    app.product_sale_price_past_list.pop(0)

    #updates the screen with the new product prices
    if len(app.query("#sales_sale_list")) > 0:
        sales_left_pane_table = app.query("#sales_sale_list").first()
        sales_left_pane_table.clear()

    #after the end_day button is pressed the product price plot is updated
    sales_select_product = app.query("#sales_select_product")
    if len(sales_select_product.nodes) > 0:
        if sales_select_product.first().value != Select.BLANK:
            sales_select_field_index = sales_select_product.first().value - 1
            selected_product = app.products[sales_select_field_index].id
        else:
            selected_product = app.products[0].id
        
        sale_prices = [product["sale_price"] for day in app.product_sale_price_past_list for product in day if product["id"] == selected_product]
        dates = datetimes_to_string([product["date"] for day in app.product_sale_price_past_list for product in day if product["id"] == selected_product])
        plt = app.query_one(SalesScreenPlot)
        plt.data = sale_prices
        plt.time = dates
        plt.replot(dates=dates, sale_prices=sale_prices)

        upper_middle_table = app.sales_screen.query("#sales_price_inventory_table").first()
        lower_middle_table = app.sales_screen.query("#sales_customer_order_table").first()
        upper_right_modifier_static = app.sales_screen.query("#sales_modifier").first()

        upper_middle_table.clear()
        lower_middle_table.clear()

        if not upper_middle_table.columns:
            upper_middle_table.add_column("ID")
            upper_middle_table.add_column("PRODUCT TYPE")
            upper_middle_table.add_column("SALE PRICE")
            upper_middle_table.add_column("PRODUCTION COST")
            upper_middle_table.add_column("PROFITIT/LOSS")
            upper_middle_table.add_column("INVENTORY")
        for product in app.sales_screen.products:
            upper_middle_table.add_row(product.id, product.product_type, product.sale_price, product.production_cost, product.exchange, app.sales_screen.warehouse.product_storage[product.id])

        if not lower_middle_table.columns:
            lower_middle_table.add_column("ID")
            lower_middle_table.add_column("PRODUCT TYPE")
            lower_middle_table.add_column("QUANTITIY")
        for order in app.sales_screen.customer_order_list:
            lower_middle_table.add_row(order[0], order[1], order[2])

        modifier_string = ""
        for modifier in app.sales_screen.sales_modifiers_list:
            if "decrease" in modifier['text']:
                color = "[red]"
            elif "increase" in modifier['text']:
                color = "[bold green]"
            modifier_string += f"{color}{modifier['text']} in price for {modifier['type']}[/]\n"
        upper_right_modifier_static.update(modifier_string)
        app.sales_screen.refresh()
        upper_right_modifier_static.update(modifier_string)

    #resets the selling_dict to 0
    for item in selling_dict:
        selling_dict[item] = 0
#<---------------END_SALES---------------->
#<---------------PROCUREMENT---------------->
    new_procurement_modifiers_list = generate_procurement_modifier(raw_materials=raw_materials)
    app.procurement_modifiers_list.clear()
    for item in new_procurement_modifiers_list:
        app.procurement_modifiers_list.append(item)

    #updates the raw material prices
    current_day_raw_material_cost_list = [{'code': raw_material.code, 'cost': raw_material.cost, 'date': app.current_date} for raw_material in app.raw_materials]
    app.raw_material_cost_past_list.append(current_day_raw_material_cost_list)
    app.raw_material_cost_past_list.pop(0)

    if len(app.query("#procurement_screen").nodes) > 0:
        selected_material = app.procurement_screen.raw_materials[0].code
        raw_material_costs = [raw_material["cost"] for day in app.procurement_screen.raw_material_cost_past_list for raw_material in day if raw_material["code"] == selected_material]
        dates = datetimes_to_string([raw_material["date"] for day in app.procurement_screen.raw_material_cost_past_list for raw_material in day if raw_material["code"] == selected_material])

        plt = app.procurement_screen.query_one(ProcurementScreenPlot)
        plt.data = raw_material_costs
        plt.time = dates
        plt.replot(dates=dates, costs=raw_material_costs)

        upper_right_modifier_static = app.procurement_screen.query("#procurement_modifier").first()
        modifier_string = ""
        for modifier in app.procurement_screen.procurement_modifiers_list:
            if "decrease" in modifier['text']:
                color = "[red]"
            elif "increase" in modifier['text']:
                color = "[bold green]"
            modifier_string += f"{color}{modifier['text']} in price for {modifier['type']}[/]\n"
        upper_right_modifier_static.update(modifier_string)


        for index, raw_material in enumerate(app.procurement_screen.raw_materials):
            app.procurement_screen.query(ProcurementWidget).first().remove()
            new_procurement_widget = ProcurementWidget(raw_material=raw_material, app=app.procurement_screen, id=f"{raw_material.code}")
            app.procurement_screen.query("#procurement-left-pane").first().mount(new_procurement_widget)

            app.procurement_screen.refresh()

#<---------------END_PROCUREMENT---------------->
#<---------------PRODUCTION---------------->
    for workcenter in app.workcenters:
        if workcenter.active == True:
            workcenter.run_all_stations()
    
    for workorder in app.workorders:
        for product_text in workorder.loaded_products:
            product = [product for product in app.products if product.id == product_text][0]
            workorder_status = workorder.are_all_parts_assembled(product_text)
            if workorder_status == True:
                if workorder.finished[product.id] == False:
                    warehouse.product_storage[product_text] += workorder.loaded_products[product_text]
                    workorder.finished[product.id] = True
                #for index, operation in enumerate(workorder.wo_assembly_operations):
                    #if operation.product_id == product_text:
                        #workorder.wo_assembly_operations.pop(index)
                        #for i, opr in enumerate(operation.workcenter.operations):
                            #if opr.id == operation.id:
                                #opr.workcenter.operations.pop(i)
                workorder.all_parts_manufactured[product.id] = False

    if len(app.query("#production_screen").nodes) > 0:

        production_datatable = app.production_screen.query("#production-datatable").first()
        production_datatable_totalwork = app.production_screen.query("#production-total-work").first()
        production_select_opr = app.production_screen.query("#production-select-opr").first()

        if app.production_screen.active_workcenter_text != "":
            workcenter = [workcenter for workcenter in app.workcenters if workcenter.id == app.production_screen.active_workcenter_text][0]
        else:
            workcenter = workcenters[0]

        if "ASS" not in f"{workcenter.id}":
            production_datatable.clear()
            production_datatable_totalwork.clear()
            for i in range(len(app.production_screen.workcenters)):
                app.production_screen.query(f"#{app.production_screen.workcenters[i].id}-1").first().remove_class("production-add-border")

            if app.production_screen.active_workcenter_text != "":
                app.production_screen.query(f"#{app.production_screen.active_workcenter_text}-1").first().add_class("production-add-border")

            columns = []
            for column in production_datatable_totalwork.columns:
                columns.append(column)
            for column in columns:
                production_datatable_totalwork.remove_column(column)

            current_operations_total_work = sum(operation.remaining_work for workcenter in app.production_screen.workcenters for operation in workcenter.operations if workcenter.id == app.production_screen.active_workcenter_text)
            if not production_datatable_totalwork.columns:
                production_datatable_totalwork.add_column("WORKCENTER ID")
                production_datatable_totalwork.add_column("TOTAL WORK")
            production_datatable_totalwork.add_row(workcenter.id, current_operations_total_work)

            columns = []
            for column in production_datatable.columns:
                columns.append(column)
            for column in columns:
                production_datatable.remove_column(column)

            if not production_datatable.columns:
                production_datatable.add_column("NO")
                production_datatable.add_column("OPERATION ID")
                production_datatable.add_column("PRODUCT ID")
                production_datatable.add_column("PART ID")
                production_datatable.add_column("WORKORDER ID")
                production_datatable.add_column("TASK")
                production_datatable.add_column("UNFINISHED STOCK")
                production_datatable.add_column("NEEDED AMOUNT")
                production_datatable.add_column("REMAINING WORK")
            for index2, operation in enumerate(workcenter.operations):
                workorder = [workorder for workorder in workorders if workorder.id == operation.workorder_id][0]
                is_product_of_workorder_finished = workorder.finished[operation.product_id]
                if not is_product_of_workorder_finished: 
                    unfinished_part_stock = app.production_screen.warehouse.check_unfinished_part_stocks(operation.loaded_part.id)
                    production_datatable.add_row(index2+1, operation.id, operation.product_id, operation.loaded_part.id, operation.workorder_id, operation.task, unfinished_part_stock,
                                                (operation.part_amount * operation.product_amount), f"{operation.remaining_work} turns") 
            opr_list = []
            for operation in workcenter.operations:
                opr_list.append((operation.id, operation.id))
            production_select_opr.set_options(opr_list)
        elif "ASS" in app.production_screen.active_workcenter_text:
            production_datatable.clear()
            production_datatable_totalwork.clear()

            columns = []
            for column in production_datatable_totalwork.columns:
                columns.append(column)
            for column in columns:
                production_datatable_totalwork.remove_column(column)

            if not production_datatable_totalwork.columns:
                production_datatable_totalwork.add_column("NO")
                production_datatable_totalwork.add_column("PRODUCT ID")
                production_datatable_totalwork.add_column("PRODUCT COUNT")
                production_datatable_totalwork.add_column("WORKORDER ID")
                production_datatable_totalwork.add_column("ALL PARTS READY")

            for workorder in app.production_screen.workorders:
                for index, product_text in enumerate(workorder.loaded_products):
                    if workorder.loaded_products[product_text] != 0:
                        product = [product for product in app.production_screen.products if product.id == product_text][0]
                        are_all_parts_available = product.check_stock_for_assembly(app.production_screen.warehouse, workorder.loaded_products[product_text], workorder)
                        production_datatable_totalwork.add_row(index+1, product_text, workorder.loaded_products[product_text], workorder.id, are_all_parts_available)

            columns = []
            for column in production_datatable.columns:
                columns.append(column)
            for column in columns:
                production_datatable.remove_column(column)

            if not production_datatable.columns:
                production_datatable.add_column("NO")
                production_datatable.add_column("OPERATION ID")
                production_datatable.add_column("PRODUCT ID")
                production_datatable.add_column("PART ID")
                production_datatable.add_column("WORKORDER ID")
                production_datatable.add_column("TASK")
                production_datatable.add_column("FINISHED STOCK")
                production_datatable.add_column("NEEDED AMOUNT")
                production_datatable.add_column("REMAINING WORK")
            for index2, operation in enumerate(workcenter.operations):
                workorder = [workorder for workorder in workorders if workorder.id == operation.workorder_id][0]
                is_product_of_workorder_finished = workorder.finished[operation.product_id]
                if not is_product_of_workorder_finished: 
                    finished_part_stock = app.production_screen.warehouse.check_finished_part_stocks(operation.loaded_part.id)
                    production_datatable.add_row(index2+1, operation.id, operation.product_id, operation.loaded_part.id, operation.workorder_id, operation.task, finished_part_stock,
                                                (operation.part_amount * operation.product_amount), f"{operation.remaining_work} turns") 

#<---------------END_PRODUCTION---------------->
    return return_dict

def end_turn():
    pass

def welcome():
    pass

def generate_sale_modifier(products, workcenters):
    product_types = products[0].product_types
    sales_modifiers_list = []

    modifier_texts = ["Great increase", "Major increase", "Minor increase", "Minor decrease", "Major decrease", "Great decrease"]
    modifiers = [1.5, 1.3, 1.15, 0.85, 0.7, 0.5]
    modifier_weight = [1, 2, 3, 3, 2, 1]
    for i in range(len(product_types)):
        modifier_dict = {}
        modifier = random.choices(modifiers, weights=modifier_weight, k=1)[0]
        product_type = product_types[i]
        for j in range(len(modifiers)):
            if modifier == modifiers[j]:
                modifier_text = modifier_texts[j]

        modifier_dict["type"] = product_type
        modifier_dict["value"] = modifier
        modifier_dict["text"] = modifier_text
        sales_modifiers_list.append(modifier_dict)
    
    for product in products:
        base_cost = product.calculate_base_cost(workcenters)
        for modifier in sales_modifiers_list:
            if product.product_type == modifier["type"]:
                if modifier["value"] == 1.5:
                    product.permanent_modifier += 0.1
                elif modifier["value"] == 0.5:
                    product.permanent_modifier -= 0.1
                product.production_cost = base_cost
                product.sale_price = base_cost * modifier["value"] * product.permanent_modifier
                product.exchange = product.sale_price - product.production_cost
                
    return sales_modifiers_list

def generate_procurement_modifier(raw_materials):
    raw_material_names = [raw_material.name for raw_material in raw_materials]
    procurement_modifiers_list = []

    modifier_texts = ["Great increase", "Major increase", "Minor increase", "Minor decrease", "Major decrease", "Great decrease"]
    modifiers = [0.2, 0.15, 0.1, -0.1, -0.15, -0.2]
    modifier_weight = [1, 2, 3, 3, 2, 1]
    for i in range(len(raw_material_names)):
        modifier_dict = {}
        modifier = random.choices(modifiers, weights=modifier_weight, k=1)[0]
        raw_material_name = raw_material_names[i]
        for j in range(len(modifiers)):
            if modifier == modifiers[j]:
                modifier_text = modifier_texts[j]

        modifier_dict["type"] = raw_material_name
        modifier_dict["value"] = modifier
        modifier_dict["text"] = modifier_text
        procurement_modifiers_list.append(modifier_dict)
    
    for raw_material in raw_materials:
        base_cost = raw_material.cost
        for modifier in procurement_modifiers_list:
            if raw_material.name == modifier["type"]:
                if modifier["value"] == 0.2:
                    raw_material.permanent_modifier += 0.05
                elif modifier["value"] == -0.2:
                    raw_material.permanent_modifier -= 0.05
                raw_material.cost = round(base_cost + (base_cost * modifier["value"]) * raw_material.permanent_modifier, 0)
    return procurement_modifiers_list

def generate_customer_order_data(products, workcenters, modifier = 1):
    """ Generates customer order data. The player may or may not choose to fullfill these orders. Creates
    a multiplier consisting the total amount of turns needed to manufacture the product and the amount of
    workcenter operators who will do the work. The idea is to get higher number of orders for products
    that consists fewer amounts of parts and fewer amounts of orders for products that consist many parts.
    The number of orders also increase as the capacity of the factory increases.
    """
    BALANCING_MULTIPLIER = 100
    STD_DEV_BALANCER = 3

    product_types = [product.product_type for product in products]
    product_ids = [product.id for product in products]
    product_operation_turncounts = [product.total_operation_turncount for product in products]

    total_workcenter_capacity = sum(workcenter.operator_count for workcenter in workcenters if workcenter.station_count != 10)
    
    product_quantity_multiplier = [total_workcenter_capacity/prod_opr_turncount for prod_opr_turncount in product_operation_turncounts]
    product_quantity_multiplier_balanced_modified = [multiplier * BALANCING_MULTIPLIER * modifier for multiplier in product_quantity_multiplier]
    product_quantity_multiplier_randomized = [random.normalvariate(multiplier, multiplier/STD_DEV_BALANCER) for multiplier in product_quantity_multiplier_balanced_modified] 

    product_quantity = [[product_ids[i], product_types[i], math.floor(product_quantity_multiplier_randomized[i])] for i in range(len(product_ids))]
    return product_quantity

def initial_product_price_history_generation(products, workcenters, current_date):
    TIME_RANGE = 29
    date = current_date - timedelta(days=TIME_RANGE)
    product_price_data_total = []
    for i in range(TIME_RANGE):
        product_price_data_perday = []
        generate_sale_modifier(products=products, workcenters=workcenters)
        for product in products:
            plot_info = {}
            plot_info["id"] = product.id 
            plot_info["sale_price"] = product.sale_price
            plot_info["date"] = date
            product_price_data_perday.append(plot_info)
        date += timedelta(days=1)
        product_price_data_total.append(product_price_data_perday)
    return product_price_data_total

def initial_raw_material_cost_history_generation(current_date, raw_materials):
    TIME_RANGE = 29
    date = current_date - timedelta(days=TIME_RANGE)
    raw_material_cost_data_total = []
    for i in range(TIME_RANGE):
        raw_material_cost_data_perday = []
        generate_procurement_modifier(raw_materials=raw_materials)
        for raw_material in raw_materials:
            plot_info = {}
            plot_info["code"] = raw_material.code
            plot_info["cost"] = raw_material.cost
            plot_info["date"] = date
            raw_material_cost_data_perday.append(plot_info)
        date += timedelta(days=1)
        raw_material_cost_data_total.append(raw_material_cost_data_perday)
    return raw_material_cost_data_total
        
def initial_machine_data_generation(lg, md, sm, warehouse, products, workorders, raw_materials, 
                                    production_methods, part_name_data, workcenters, selling_dict, 
                                    planning_dict, raw_materials_dict, raw_material_mapping):
    """ generates machine info if it does not already exist """

    endproduct_lg = []
    endproduct_md = []
    endproduct_sm = []
    for i in range(lg):
        production_type_leaning = random.choices(production_methods, k=1)[0]
        raw_material_codes = [raw_material.code for raw_material in raw_materials for prod_type in raw_material.prod_types if prod_type == production_type_leaning] 

        raw_material_code_indexes = []
        for code in raw_material_codes:
            for index, item in enumerate(raw_materials_dict):
                if code == item:
                    raw_material_code_indexes.append(index)

        leaning_weights = [1,1,1,1,1,1,1,1,1,1]
        for item in raw_material_code_indexes:
            leaning_weights[item] = 3
        
        endproduct_lg.append(Product('LG', warehouse=warehouse, products=products, workorders=workorders, 
                                raw_materials=raw_materials, production_methods=production_methods,
                                part_name_data=part_name_data, workcenters=workcenters, selling_dict=selling_dict,
                                planning_dict=planning_dict, leaning_weights=leaning_weights, 
                                production_type_leaning=production_type_leaning))
    for i in range(md):
        production_type_leaning = random.choices(production_methods, k=1)[0]
        raw_material_codes = [raw_material.code for raw_material in raw_materials for prod_type in raw_material.prod_types if prod_type == production_type_leaning] 

        raw_material_code_indexes = []
        for code in raw_material_codes:
            for index, item in enumerate(raw_materials_dict):
                if code == item:
                    raw_material_code_indexes.append(index)

        leaning_weights = [1,1,1,1,1,1,1,1,1,1]
        for item in raw_material_code_indexes:
            leaning_weights[item] = 10
        endproduct_md.append(Product('MD', warehouse=warehouse, products=products, workorders=workorders,
                                raw_materials=raw_materials, production_methods=production_methods,
                                part_name_data=part_name_data, workcenters=workcenters, selling_dict=selling_dict,
                                planning_dict=planning_dict, leaning_weights=leaning_weights,
                                production_type_leaning=production_type_leaning)) 
    for i in range(sm):
        production_type_leaning = random.choices(production_methods, k=1)[0]
        raw_material_codes = [raw_material.code for raw_material in raw_materials for prod_type in raw_material.prod_types if prod_type == production_type_leaning] 

        raw_material_code_indexes = []
        for code in raw_material_codes:
            for index, item in enumerate(raw_materials_dict):
                if code == item:
                    raw_material_code_indexes.append(index)

        leaning_weights = [1,1,1,1,1,1,1,1,1,1]
        for item in raw_material_code_indexes:
            leaning_weights[item] = 10
        endproduct_sm.append(Product('SM', warehouse=warehouse, products=products, workorders=workorders,
                                raw_materials=raw_materials, production_methods=production_methods, 
                                part_name_data=part_name_data, workcenters=workcenters, selling_dict=selling_dict,
                                planning_dict=planning_dict, leaning_weights=leaning_weights,
                                production_type_leaning=production_type_leaning))

    end_products_all = endproduct_lg + endproduct_md + endproduct_sm
    return end_products_all 

def initial_workcenter_data_generation(warehouse, workcenters, production_methods, products, workorders):
    """ generates workcenter info if it does not already exist """
    for item in production_methods:
        workcenters.append(WorkCenter(prod_method=item, warehouse=warehouse, workcenters=workcenters,
                                        workorders=workorders, products=products))
    return workcenters

def initial_raw_material_generation(app):
    """ generates raw material objects for each item in raw_materials dict """
    app.raw_materials_dict = {'S1': 'Steel Ingot', 'S2': 'Steel Sheet','S3': 'Steel Plate','S4': 'Steel_Bar',
                      'A1': 'Aluminum Ingot', 'A2': 'Aluminum Sheet', 'A3': 'Aluminum Plate', 'A4': 'Aluminum_Bar',
                      'P1': 'Plastic Pellets', 'E1': 'Electronics'}
    app.raw_material_mapping = {'Machining': ['S3', 'A3'], 'Bending': ['S2', 'A2'], 'Casting': ['S1', 'A1', 'P1'], 'Forging': ['S4', 'A4'], 
                            'Paintjob': ['A2', 'A3', 'A4', 'S2', 'S3'], 'Welding': ['S2', 'S3', 'S4']}
    
    raw_materials = []
    for raw_material_code in app.raw_materials_dict:
        raw_material_production_methods = [production_type for production_type in app.raw_material_mapping for code in app.raw_material_mapping[production_type] if code == raw_material_code]
        raw_material_name = app.raw_materials_dict[raw_material_code]
        raw_materials.append(RawMaterial(raw_material_code, raw_material_name, raw_material_production_methods, app.warehouse))
    return raw_materials

def part_names_csv_reader():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, 'part_names.csv')
    with open(file_path, mode='r') as file:
        csv_dict_reader = csv.DictReader(file)
        data = [row for row in csv_dict_reader]
    return data

def allocate_workcenter(operation, workcenters):
    for workcenter in workcenters:
        if workcenter.prod_method == operation.task:
            workcenter.operations.append(operation)
            operation.workcenter = workcenter

class WorkOrder:
    def __init__(self, loaded_products, workorders, current_date, operations, products, workcenters, warehouse):
        self.id = f"WO-{current_date.day}/{current_date.month}/{current_date.year}-{len(workorders) + 1}"
        self.loaded_products = {key: loaded_products[key] for key in loaded_products}
        self.loaded_products_transfer_status = {key: False for key in loaded_products}
        self.date = current_date
        self.wo_operations = []
        self.wo_assembly_operations = []
        self.existing_operations = operations
        self.all_parts_manufactured = {key: False for key in loaded_products}
        self.products = products
        self.warehouse = warehouse
        self.finished = {key: False for key in loaded_products}

        for product_id in self.loaded_products:
            current_product = [product for product in products if product.id == product_id][0]
            product_amount = self.loaded_products[product_id]
            if product_amount != 0:
                for part in current_product.product_parts:
                    part_amount=current_product.part_amounts[part.id]
                    for index, operation in enumerate(part.operations):
                        remaining_work = part.operation_times[index] * part_amount * product_amount

                        new_operation = Operation(workorder_id=self.id,task=operation,operations=self.existing_operations,
                                                            loaded_part=part,product=current_product,remaining_work=remaining_work,
                                                            product_amount=product_amount,part_amount=part_amount)
                        self.wo_operations.append(new_operation)
                        self.existing_operations.append(new_operation)
                        
                        allocate_workcenter(workcenters=workcenters, operation=new_operation)

                    remaining_assembly = part.assembly_time * part_amount * product_amount
                    new_assembly_operation = Operation(workorder_id=self.id,task="Assembly",operations=self.existing_operations,
                                                            loaded_part=part,product=current_product,remaining_work=remaining_assembly,
                                                            product_amount=product_amount,part_amount=part_amount)
                    self.wo_assembly_operations.append(new_assembly_operation)
                    self.existing_operations.append(new_assembly_operation)
                    allocate_workcenter(workcenters=workcenters, operation=new_assembly_operation)

    #def are_all_parts_manufactured(self, product_text):
    #    product = [product for product in self.products][0]
    #    self.all_parts_manufactured[product_text] = product.check_stock_for_assembly(self.warehouse, self.loaded_products[product_text])

    def are_all_parts_assembled(self, product_text):
        flag = True
      
        for operation in self.wo_assembly_operations:
            if operation.product_id == product_text:
                if operation.remaining_work > 0:
                    flag = False
                    break
        return flag

class Operation:
    def __init__(self, workorder_id, task, product, operations, loaded_part, remaining_work, product_amount, part_amount):
        while True:
            digits = "".join(random.choices(string.digits, k=6))
            generated_opr_number = f"OPR-{digits}-{len(operations) + 1}"
            existing_opr_numbers = [operation.id for operation in operations]
            if generated_opr_number not in existing_opr_numbers:
                self.id = generated_opr_number
                break

        self.product_id = product.id
        self.loaded_part = loaded_part
        self.raw_material = self.loaded_part.raw_material_name
        self.workorder_id = workorder_id
        self.task = task
        self.part_amount = part_amount
        self.product_amount = product_amount
        self.remaining_work = remaining_work
        self.workcenter = None
     
class WorkCenter:
    def __init__(self, prod_method, warehouse, workcenters, workorders, products):
        DEFAULT_FAIL_RATE = 0.02
        DEFAULT_FAULTY_PART_RATE = 0.05
        DEFAULT_OPERATING_COST = 50
        DEFAULT_STATION_COUNT = 2
        DEFAULT_OPERATOR_COUNT = 2
        self.warehouse = warehouse
        self.workorders = workorders
        self.products = products

        while True:
            digits = ''.join(random.choices(string.digits, k=6))
            generated_id = prod_method[:3].upper() + digits

            self.id = ''
            existing_ids = [workcenter.id for workcenter in workcenters]
            if generated_id not in existing_ids:
                self.id = generated_id
                break

        self.operating_cost = DEFAULT_OPERATING_COST
        self.prod_method = prod_method
        self.fail_rate = DEFAULT_FAIL_RATE
        self.faulty_part_rate = DEFAULT_FAULTY_PART_RATE
        self.progress = 0
        self.active = False
        self.faulty = False
        if self.prod_method == "Paintjob":
            self.station_count = DEFAULT_STATION_COUNT + 1
        else:
            self.station_count = DEFAULT_STATION_COUNT
        self.operator_count = DEFAULT_OPERATOR_COUNT
        self.operations = []

    def __str__(self):
        return ("Workcenter ID: " + str(self.id) + "\n" +
                "Production Method: " + self.prod_method + "\n" +
                "Fail Rate: " + str(self.fail_rate) + "%\n" +
                "Active: " + str(self.active) + "\n" +
                "Station Count: " + str(self.station_count) + "\n" +
                "Operator Count: " + str(self.operator_count) + "\n" +
                "Faulty Part Rate: " + str(self.faulty_part_rate) + "%\n")
    
    def add_operation(self, operation):
        self.operations.append(operation)

    def add_operator(self):
        if self.operator_count < self.station_count:
            self.operator_count += 1
            print("Operator successfully added.")
        else:
            print("Not enough stations.")

    def add_station(self):
        self.station_count += 1

    def run(self, operation):
        loaded_part = operation.loaded_part

        #if random.random() > self.fail_rate:
        #    self.active = False
        
        if self.active:
            shelf, part_address = [(shelf, address) for shelf in self.warehouse.shelves for address in shelf.addresses if shelf.addresses[address] == loaded_part.id][0]
            #if shelf.unfinished_part_stocks[part_address] != 0: 
                #shelf.being_worked_on[part_address] += operation.part_amount
                #shelf.unfinished_part_stocks[part_address] -= operation.part_amount
            #if random.random() < self.faulty_part_rate:

            operation.remaining_work -= 1
            if  operation.remaining_work == 0:
                if loaded_part.operations_done < len(loaded_part.operations) - 1:
                    loaded_part.operations_done += 1
                    #shelf.finished_part_stocks[part_address] += operation.part_amount
                    #shelf.unfinished_part_stocks[part_address] -= operation.part_amount
                else:
                    loaded_part.operations_done = 0
                    shelf.finished_part_stocks[part_address] += operation.part_amount
                    shelf.unfinished_part_stocks[part_address] -= operation.part_amount
            #else:
            #    self.progress = 0
            #    shelve.faulty[part_address] += 1
            #    number -= 1

    def ass_run(self, operation):
        loaded_part = operation.loaded_part

        if self.active:
            shelf, part_address = [(shelf, address) for shelf in self.warehouse.shelves for address in shelf.addresses if shelf.addresses[address] == loaded_part.id][0]
            operation.remaining_work -= 1
            if  operation.remaining_work == 0:
                shelf.finished_part_stocks[part_address] -= operation.part_amount

    def run_all_stations(self):
        operations_run = 0
        i = 0
        while True:
            if i < len(self.operations):
                if self.operations[i].remaining_work > 0:
                    if 'ASS' not in self.id:
                        unfinished_part_stock = self.warehouse.check_unfinished_part_stocks(self.operations[i].loaded_part.id)
                        if self.operations[i].part_amount <= unfinished_part_stock:
                            self.run(self.operations[i])
                            operations_run += 1
                    else:
                        workorder = [workorder for workorder in self.workorders if workorder.id == self.operations[i].workorder_id][0]
                        product = [product for product in self.products if product.id == self.operations[i].product_id][0]
                        are_all_parts_available = product.check_stock_for_assembly(self.warehouse, workorder.loaded_products[product.id], workorder)

                        if are_all_parts_available:
                            finished_part_stock = self.warehouse.check_finished_part_stocks(self.operations[i].loaded_part.id)
                            if self.operations[i].part_amount <= finished_part_stock:
                                self.ass_run(self.operations[i])
                                operations_run += 1
                i += 1
                if operations_run >= self.operator_count:
                    break
            else:
                break

class Assembly(WorkCenter):
    def __init__(self, warehouse, workcenters, workorders, products):
        super().__init__(warehouse=warehouse, workcenters=workcenters, prod_method="Assembly",
                         products=products, workorders=workorders)
        DEFAULT_STATION_COUNT = 10
        DEFAULT_OPERATOR_COUNT = 3
        self.station_count = DEFAULT_STATION_COUNT
        self.operator_count = DEFAULT_OPERATOR_COUNT

class Warehouse:
    def __init__(self):
        self.shelves = []
        self.product_storage = {}
        self.raw_material_stocks = {}
        
    def __str__(self):
        shelf_codes = [shelve.shelve_code for shelve in self.shelves]
        return ("Shelves: " + shelf_codes + "\n")
    
    def check_unfinished_part_stocks(self, part_code):
        for shelve in self.shelves:
            for address in shelve.addresses:
                if shelve.addresses[address] == part_code: 
                    return shelve.unfinished_part_stocks[address]
        return None
    
    def check_finished_part_stocks(self, part_code):
        for shelve in self.shelves:
            for address in shelve.addresses:
                if shelve.addresses[address] == part_code: 
                    return shelve.finished_part_stocks[address]
        return None
                
    def add_shelf(self):
        all_shelf_codes = string.ascii_uppercase
        existing_shelf_codes = [shelf.code for shelf in self.shelves]
        code = [letter for letter in all_shelf_codes if letter not in existing_shelf_codes][0]
        self.shelves.append(Shelf(code))
        return self.shelves[-1], code

    def allocate_space_to_part(self, part_number, part_name):
        shelf, address = self.check_shelf_space()
        shelf.addresses[address] = part_number
        shelf.partnames[address] = part_name
        return address
    
    def add_finished_stock(self,part_number):
        for shelf in self.shelves:
            for address in shelf.addresses:
                if shelf.addresses[address] == part_number:  
                    shelf.finished_part_stocks[address] += 1
    def add_unfinished_stock(self,part_number):
        for shelf in self.shelves:
            for address in shelf.addresses:
                if shelf.addresses[address] == part_number:  
                    shelf.unfinished_part_stocks[address] += 1  

    def check_shelf_space(self):
        for shelf in self.shelves:
            for address in shelf.addresses:
                if shelf.addresses[address] == '':
                    return shelf, address
        new_shelf, code = self.add_shelf()
        initial_address = code + "1"
        return new_shelf, initial_address

class Shelf:
    def __init__(self, code):

        STORAGE_LIMIT = 101
        self.code = code
        self.addresses = {f"{code}{str(num)}": '' for num in range(1,STORAGE_LIMIT)}
        self.finished_part_stocks = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}
        self.being_worked_on = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}
        self.unfinished_part_stocks = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}
        self.partnames = {f"{code}{str(num)}": '' for num in range(1,STORAGE_LIMIT)}

        #self.on_the_way_stocks = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}
        #self.faulty_part_stocks = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}
        #self.being_used_in_assembly = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}
        #self.faulty = {f"{code}{str(num)}": 0 for num in range(1,STORAGE_LIMIT)}

    def add_part():
        pass

    def __str__(self):
        return ("Shelf Adress: " + str(self.addresses) + "-- Finshed: " + {self.finished_part_stocks} + "-- Unfinished: " + {self.unfinished_part_stocks} + "-- On The Way: " + {self.on_the_way_stocks} + "\n")

class Product:
    def __init__(self, size, warehouse, products, workorders, raw_materials, production_methods, 
                 part_name_data, workcenters, selling_dict, planning_dict, leaning_weights,
                 production_type_leaning):
        part_counts = {
            'LG': 40,
            'MD': 20,
            'SM': 10,
            }
        self.product_types = [key for key in part_name_data[0]] 
        self.raw_materials = raw_materials
        self.raw_materials_need = {}
        while True:
            digits = ''.join(random.choices(string.digits, k=6))
            generated_product_number = 'E' + digits + size

            #self.id = ''
            existing_product_numbers = [product.id for product in products]
            if generated_product_number not in existing_product_numbers:
                self.id = generated_product_number
                break
        
        self.production_type_leaning = production_type_leaning
        self.part_count = part_counts.get(size, 0) + random.randint(-5, 5)
        self.product_type = self.product_types[random.randint(0,6)]

        self.product_parts = [Part(self, warehouse, raw_materials, production_methods, part_name_data, self.product_type, leaning_weights, production_type_leaning) for i in range(self.part_count)]

        amounts = [1, 2, 3, 4, 5, 6, 7, 8]
        weights_amounts = [10, 3, 1, 1, 1, 1, 1, 1]

        self.part_amounts = {part.id: random.choices(amounts, weights=weights_amounts, k=1)[0] for part in self.product_parts}
        selling_dict[self.id] = 0
        planning_dict[self.id] = 0

        self.production_cost = self.calculate_base_cost(workcenters=workcenters)
        for i in range(len(part_counts)): # makes the larger machines more profitable
            if self.id[-2:] == "LG":
                profit_balancer = 1.4
            elif self.id[-2:] == "MD":
                profit_balancer = 1.2
            else:
                profit_balancer = 1

        self.permanent_modifier = profit_balancer
        self.sale_price =  self.production_cost *  self.permanent_modifier
        #warehouse.product_storage[self.id] = math.floor(15000/self.sale_price)
        warehouse.product_storage[self.id] = 0
        self.exchange = self.production_cost - self.sale_price
        
        self.total_assembly_time = sum(part.assembly_time * self.part_amounts[part.id] for part in self.product_parts)
        self.total_manufacturing_time = sum(part.operation_times[i] * self.part_amounts[part.id] for part in self.product_parts for i in range(len(part.operation_times)))

    def calculate_base_cost(self, workcenters):
        total_raw_part_cost = sum(part.raw_material.cost * self.part_amounts[part.id] for part in self.product_parts)
        operation_times = [operation_time for part in self.product_parts for operation_time in part.operation_times]
        self.total_operation_turncount = sum(sum(part.operation_times) * self.part_amounts[part.id]  for part in self.product_parts)
        default_operating_cost = workcenters[0].operating_cost
        base_operating_cost = self.total_operation_turncount * default_operating_cost
        base_cost = total_raw_part_cost + base_operating_cost
        return base_cost

    def list_part_amounts(self):
        for item in self.part_amounts:
            print(f"{item}: {self.part_amounts[item]}")
    
    def calculate_raw_material_need(self, workorder):
        for raw_material in self.raw_materials:
            self.raw_materials_need[raw_material.code] = 0
        for part in self.product_parts:
            part_count = self.part_amounts[part.id]
            self.raw_materials_need[part.raw_material.code] += part_count * workorder.loaded_products[self.id]
        return self.raw_materials_need
    
    def check_stock_for_assembly(self, warehouse, prd_count, workorder):
        flag = workorder.all_parts_manufactured[self.id]
        if prd_count == 0:
            prd_count = 1
        if flag == False:
            flag = True
            for part in self.product_parts:
                stock = warehouse.check_finished_part_stocks(part.id)
                #stock = sum(shelf.finished_part_stocks[key] for shelf in warehouse.shelves for key, part_id in shelf.addresses.items() if part.id == part_id)
                need = self.part_amounts[part.id] * prd_count
                if need > stock:
                    flag = False
                    break
        if flag == True:
            workorder.all_parts_manufactured[self.id] = True
        return flag
        
class Part:
    def __init__(self, current_product, warehouse, raw_materials, production_methods, part_name_data, product_type, leaning_weights, production_type_leaning):

        assembly_times = [1, 1, 1, 2, 3]
        weights_assembly_times = [5, 4, 3, 2, 1]
        self.assembly_time = random.choices(assembly_times, weights=weights_assembly_times, k=1)[0]

        lead_times = [2, 5, 7, 10, 13]
        weights_lead_times = [3, 3, 3, 2, 1]
        self.lead_time = random.choices(lead_times, weights=weights_lead_times, k=1)[0]

        self.raw_material = random.choices(raw_materials, weights=leaning_weights, k=1)[0]
        self.raw_material_name = self.raw_material.name
        raw_material_operation_count = len(self.raw_material.prod_types)
        if self.raw_material.code not in ["E1"]:
            if production_type_leaning in self.raw_material.prod_types:
                index = self.raw_material.prod_types.index(production_type_leaning)
            else:
                index = None
            prod_weights = []
            for i in range(len(self.raw_material.prod_types)):
                if i == index:
                    prod_weights.append(4)
                else:
                    prod_weights.append(1)
            self.operations = random.choices(self.raw_material.prod_types, weights=prod_weights, k=random.randint(1,raw_material_operation_count))
        else:
            self.operations = []
        operation_times_list = [1, 1, 1, 2, 3]
        weights_operation_times = [5, 4, 3, 2, 1]
        self.operation_times = [random.choices(operation_times_list, weights=weights_operation_times, k=1)[0] for operation in self.operations]

        digits = ''.join(random.choices(string.digits, k=6))
        self.id = 'P' + digits + self.raw_material.name.upper()[:3]

        part_names = [row[product_type] for row in part_name_data]
        self.name = random.choices(part_names, k=1)[0]

        self.part_storage_loc = warehouse.allocate_space_to_part(part_number=self.id, part_name=self.name)
        self.faulty = False

        self.operations_done = 0

    def __str__(self):
        return ("Part Number: " + str(self.id) + "\n" +
                "Part Name: " + str(self.name) + "\n" +
                "Assembly Time: " + str(self.assembly_time) + " turns\n" +
                "Raw Material Lead Time: " + str(self.lead_time) + " turns\n" +
                "Raw Material: " + str(self.raw_material.name) + "\n" +
                "Raw Material Cost: " + str(self.raw_material.cost) + "$\n" +
                "Operations: " + str(self.operations) + "\n" +
                "Operation Times: " + str(self.operation_times) + " turns\n" +
                "Part Storage Location: " + str(self.part_storage_loc) + "\n" +
                "Batch Number: " + str(self.batch_num) + "\n")

class RawMaterial:
    def __init__(self, raw_material_code, raw_material_name, raw_material_prod_types, warehouse):
        price_range = [10, 20, 30, 40 ,50, 60]
        self.cost = random.choices(price_range)[0]
        self.code = raw_material_code
        self.name = raw_material_name
        self.prod_types = raw_material_prod_types
        
        warehouse.raw_material_stocks[self.code] = 50

        self.permanent_modifier = 1
        lead_times = [2, 5, 7, 10, 13]
        weights_lead_times = [3, 3, 3, 2, 1]
        self.lead_time = random.choices(lead_times, weights=weights_lead_times, k=1)[0]

        order_quantities = [10, 20, 30, 40, 50]
        order_quantity_weights = [5, 4, 3, 2, 1]
        self.minimum_order_quantity = random.choices(order_quantities, weights=order_quantity_weights, k=1)[0]

def balance_production_line():
    pass

def get_sales_info():
    pass

if __name__ == "__main__":
    main()

