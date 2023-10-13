from .table import Table

class Table_SNG(Table):

    def __init__(self, id, *, table_type, **kwargs):
        assert table_type == "SNG"
        super().__init__(id, table_type=table_type, **kwargs)