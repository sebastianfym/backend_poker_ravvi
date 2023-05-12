class Manager:
    
    tables = {}
    
    async def dispatch_command(self, event):
        table_id = event.get('table_id', None)
        if not table_id:
            return
        table = self.tables.get(table_id, None)
        if not table:
            return
        