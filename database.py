from supabase import create_client, Client
from dotenv import load_dotenv
import os



class DataBase():
    def __init__(self, url, key):
        self.supabase: Client = create_client(url, key)

    #* получаем все данные из указанной таблицы
    def get_all(self, table_name):
        return self.supabase.table(table_name).select('*').execute()
    
    #* получаем данные из нужной ячейки
    def get_data(self, table_name, coll_name, key, key_val):
        return self.supabase.table(table_name).select(coll_name).eq(key, key_val).execute().data

    #* метод paste_to_cell нужен для раобты с таблицей users
    def paste_to_cell_users(self, cell_name, data, key, key_val):
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

    def increment_used_promocodes(self, key, key_val):
        response = self.supabase.table('promocodes') \
            .select('used') \
            .eq(key, key_val) \
            .execute().data[0]['used']

        return self.supabase.table('promocodes').update({'used': response + 1}).eq(key, key_val).execute()

    '''
    users:
    user_id - int - not NULL
    username - str - NULL
    purchased - str - NULL
    bought_with_discount - int - NULL
    spent - int - NULL
    discount - int - not NULL
    
    receipt:
    place - str - not NULL
    user_id - int - not NULL
    payload - str - not NULL
    amount - int - not NULL
    username - str - NULL
    promocode - str - NULL

    promcodes:
    user_id - int - not NULL
    owner - str - not NULL
    name - str - not NULL
    discount - int - not NULL
    used - int - NULL
    '''
    #* добавляет строки в таблицы
    def insert_data(self, table_name, data):
        return self.supabase.table(table_name).insert(data).execute()

    #* удаляет купленные места из списка доступных
    def remove_column(self, table_name: str, row: int, col: int):
        res = self.supabase.table(table_name).select('free_column').eq('free_row', row).execute()
        if not res.data: return False
        
        current = res.data[0]['free_column']
        updated = current.replace(f'{str(col)} ', '', 1)
        
        self.supabase.table(table_name).update({'free_column': updated}).eq('free_row', row).execute()
        return current != updated

    #* проверяет свободно ли место  
    def seat_is_free(self, table_name: str, row: int, col: int):
        response = self.supabase.table(table_name).select('free_column').eq('free_row', row).execute()
        res = response.data[0]['free_column'].split(' ')
        if col in res: return True
        return False
    
    def get_column(self, table_name, col):
        res_lst = []
        response = self.supabase.table(table_name).select(col).execute().data
        for i in response: res_lst.append(i[col])
        return res_lst
    
    def update_user_data(self, table_name, data, uid):
        data_to_update = self.supabase.table(table_name).select(", ".join(data.keys())).eq('user_id', uid).execute().data[0]
        
        for i in data_to_update:
            if isinstance(data[i], int): data_to_update[i] += data[i]
            elif isinstance(data[i], str): data_to_update[i] += f' {data[i]}'

        return self.supabase.table(table_name).update(data_to_update).eq('user_id', uid).execute()
        

# load_dotenv()

# url = os.environ.get("SUPABASE_URL")
# key = os.environ.get("SUPABASE_KEY")
# supabase = create_client(url, key)
# cl = DataBase(url, key)

# print(cl.get_data('users', 'discount', 'user_id', 798330024)[0]['discount'])

# print(cl.get_data('promocodes', 'name', 'name', 'C0DEMQSPRICEOFF'))

# print(cl.increment_used_promocodes('name', 'C0DEMQSPRICEOFF'))
# print(cl.get_data('promocodes', 'discount', 'user_id', 12341234)['discount'])