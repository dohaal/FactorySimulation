import pytest
from unittest.mock import Mock
from project import Product, Warehouse, generate_sale_modifier, part_names_csv_reader, generate_procurement_modifier  # Replace 'your_module' with the actual module name

# Define fixtures for setting up test data
@pytest.fixture
def mock_warehouse_data():
    # Create mock data for product initialization
    warehouse = Warehouse()
    warehouse.add_shelf()
    for i in range(50):
        warehouse.allocate_space_to_part(f"mock_part_id_{i}", f"mock_part_name_{i}")
    for i in range(25):
        warehouse.add_finished_stock(f"mock_part_id_{i}")
    for i in range(25,50):
        warehouse.add_unfinished_stock(f"mock_part_id_{i}")
    return warehouse


def test_check_unfinished_part_stocks(mock_warehouse_data):
    assert mock_warehouse_data.shelves[0].addresses["A5"] == f"mock_part_id_{4}"
    assert mock_warehouse_data.check_unfinished_part_stocks(f"mock_part_id_{4}") == 0
    assert mock_warehouse_data.check_unfinished_part_stocks(f"mock_part_id_{34}") == 1

def test_check_finished_part_stocks(mock_warehouse_data):
    assert mock_warehouse_data.shelves[0].addresses["A5"] == f"mock_part_id_{4}"
    assert mock_warehouse_data.check_finished_part_stocks(f"mock_part_id_{4}") == 1
    assert mock_warehouse_data.check_finished_part_stocks(f"mock_part_id_{34}") == 0

def test_part_names_csv_reader():
    assert len(part_names_csv_reader()) == 100


