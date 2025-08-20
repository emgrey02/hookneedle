from app.db import get_db

def sql_data_to_list_of_dicts(select_query, options):
    """Returns data from an SQL query as a list of dicts."""
    db = get_db()

    try:
        things = db.execute(select_query, options).fetchall()
        unpacked = [{k: item[k] for k in item.keys()} for item in things]
        return unpacked
    except Exception as e:
        print(f"Failed to execute. Query: {select_query}\n with error:\n{e}")
        return []