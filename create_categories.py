from model import model

# as category table has no CRUD app
# here it create your categories
categories_names_list = ['category 1', 'category 2',
                         'category 3', 'category 4',
                         'category 5', 'category 6']


def insert_categories(names_list):
    """  create categories in catalog db
    by names provided by my_list argument"""
    for i in names_list:
        model.create_category(i)


insert_categories(categories_names_list)
