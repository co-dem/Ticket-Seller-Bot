from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

# url = os.environ.get("SUPABASE_URL")
# key = os.environ.get("SUPABASE_KEY")
# supabase = create_client(url, key)

class DataBase:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)

    def insert_data(self, table_name: str, data: dict):
        return self.supabase.table(table_name).insert(data).execute()

    def get_all(self, table_name: str):
        return self.supabase.table(table_name).select("*").execute()

    def get_by_id(self, table_name: str, item: int):
        return self.supabase.table(table_name).select("*").eq("free_row", item).execute()

    def update_data(self, table_name: str, item: int, updates: dict):
        return self.supabase.table(table_name).update(updates).eq("free_row", item).execute()
    
    def seat_is_free(self, table_name: str, row: int, column: int):
        try:
            # Получаем запись по free_row
            response = self.supabase.table(table_name)\
                .select('free_column')\
                .eq('free_row', row)\
                .execute()
            
            # Если запись не найдена
            if not response.data: return False
            
            # Получаем список колонок из первой найденной записи
            free_columns = response.data[0].get('free_column', '')
            
            # Если free_column пустой или None
            if not free_columns: return False
            
            # Преобразуем строку "1, 2, 3, 4, 5, 6, 7, 8" в список целых чисел
            columns_list = [int(col.strip()) for col in free_columns.split(',')]

            return column in columns_list
            
        except Exception as e:
            print(f"Ошибка при проверке места: {e}")
            return False
    

# cl = DataBase(url, key)

# for i in cl.get_all('places').data:
#     print(i['free_column'])