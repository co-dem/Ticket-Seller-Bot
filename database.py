from supabase import create_client, Client
from dotenv import load_dotenv
import os

# load_dotenv()

# url = os.environ.get("SUPABASE_URL")
# key = os.environ.get("SUPABASE_KEY")
# supabase = create_client(url, key)

class DataBase():
    def __init__(self, url, key):
        self.supabase: Client = create_client(url, key)

    #* получаем все данные из указанной таблицы
    def get_all(self, table_name):
        return self.supabase.table(table_name).select('*').execute()
    
    #* получаем данные из нужной ячейки
    def get_data(self, table_name, cell_name, key, key_val):
        return self.supabase.table(table_name).select(cell_name).eq(key, key_val).data[0]

    #* метод paste_to_cell нужен для раобты с таблицей users
    def paste_to_cell(self, cell_name, data, key, key_val):
        response = self.supabase.table('users') \
                .select(cell_name) \
                .eq(key, key_val) \
                .execute().data[0][cell_name]

        # если response --> str, значит операция идёт над ячейкой purchased
        # если response --> int, значит операция идёт над bought_with_discount или spent
        # т.к. bought_with_discount и spent типа int, нет разницы как и в какую добавлять data 
        if isinstance(response, str)  : response += f', {data}'
        elif isinstance(response, int): response += data

        return self.supabase.table('users').update({cell_name: response}).eq(key, key_val).execute()

    
    #* добавляет строки в таблицы
    def insert_data(self, table_name, data):
        return self.supabase.table(table_name).insert(data).execute()

    #* удаляет купленные места из списка доступных
    def remove_column(self, table_name: str, row: int, col: int):
        res = self.supabase.table(table_name).select('free_column').eq('free_row', row).execute()
        if not res.data: return False
        
        current = res.data[0]['free_column']
        updated = current.replace(str(col), '', 1)
        
        self.supabase.table(table_name).update({'free_column': updated}).eq('free_row', row).execute()
        return current != updated

    #* проверяет свободно ли место  
    def seat_is_free(self, table_name: str, row: int, col: int):
        res = self.supabase.table(table_name).select('free_column').eq('free_row', row).execute()
        return bool(res.data and str(col) in res.data[0].get('free_column', ''))
    

# cl = DataBase(url, key)