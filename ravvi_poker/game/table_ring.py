from .table import Table

class Table_RING(Table):

    def __init__(self, id, *, table_type, **kwargs):
        assert table_type == "RING_GAME"
        super().__init__(id, table_type=table_type, **kwargs)