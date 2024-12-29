# Function to create conditional background coloring, depending on table position 

def get_table_style():
    return [
        {
            'if': {'row_index': i, 'column_id': 'table_position'},
            'backgroundColor': '#66cdaa',  # Light green
            'color': 'black',
            'padding': '8px'
        } for i in range(0, 6)
    ] + [
        {
            'if': {'row_index': i, 'column_id': 'table_position'},
            'backgroundColor': '#87cefa',  # Light blue
            'color': 'black'
        } for i in range(6, 10)
    ] + [
        {
            'if': {'row_index': i, 'column_id': 'table_position'},
            'backgroundColor': '#a9a9a9',  # Grey
            'color': 'black'
        } for i in range(10, 12)
    ] + [
        {
            'if': {'row_index': i, 'column_id': 'table_position'},
            'backgroundColor': '#f08080',  # Light red
            'color': 'black'
        } for i in range(12, 14)
    ]