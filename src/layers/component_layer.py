"""
Unified Component & Lot Management Layer

Provides a single API for all component (bullet, powder, primer, brass) and lot/batch management operations.
- Facade over component_database, component_inventory, component_lot_tracker, brass_manager, batch_manager
- Used by UI, plugins, and business logic
"""

from ..database import batch_manager
from ..modules import (
    brass_manager,
    component_database,
    component_inventory,
    component_lot_tracker,
)


class ComponentLayer:
    def __init__(self):
        self.db = component_database
        self.inventory = component_inventory
        self.lot_tracker = component_lot_tracker
        self.brass = brass_manager
        self.batch = batch_manager

    # Component DB
    def load_database(self, *args, **kwargs):
        return self.db.load_component_database_json(*args, **kwargs)

    def save_database(self, *args, **kwargs):
        return self.db.save_component_database_json(*args, **kwargs)

    # Inventory
    def get_inventory(self, *args, **kwargs):
        return self.inventory

    # Lot tracking
    def add_lot(self, *args, **kwargs):
        return self.lot_tracker.AddLotDialog(*args, **kwargs)

    # Brass
    def get_brass_manager(self, *args, **kwargs):
        return self.brass.BrassManager(*args, **kwargs)

    # Batch
    def get_batch_manager(self, *args, **kwargs):
        return self.batch


component_layer = ComponentLayer()
