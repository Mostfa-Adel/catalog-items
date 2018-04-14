from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from catalogDBSetup import Base, Item, Category, User
from flask import jsonify


class Model:
    """ manage 'CRUD' operations on catalog db
    manage three tables: categories, items and
    users"""

    def __init__(self):
        self.session = self.make_session()

    @staticmethod
    def make_session():
        """make all operations to connect to catalog.db database
        and return session object to make CRUD operations with it"""
        engine = create_engine("sqlite:///catalog.db")
        Base.metadata.bind = engine
        s = sessionmaker(bind=engine)
        return s()

    # --------------------------------------
    # ----------- user methods ------------
    # -------------------------------------
    def create_user(self, login_session):
        user = User(name=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'],
                    )
        self.create(user)
        user_id = self.get_user_id(email=login_session['email'])
        return user_id

    def get_user(self, user_id):
        user = self.session.\
            query(User).\
            filter_by(id=user_id).\
            one()
        return user

    def get_user_id(self, email):
        """ get user id by email """
        try:
            user = self.session.\
                query(User).\
                filter_by(email=email).\
                one()
            return user.id
        except:
            return None

    # ---------------------------------------
    # ---------- category methods -----------
    # ---------------------------------------
    def all_categories(self):
        """ returns list of all categories"""
        categories = self.session.\
            query(Category).\
            all()
        return categories

    def get_category(self, cid):
        """ return category object by category id"""
        category = self.session.\
            query(Category).\
            filter_by(id=cid).\
            first()
        return category

    def create_category(self, name):
        """ create category by name"""
        category = Category(name=name)
        self.create(category)

    def update_category(self, obj, name):
        """ update category by giving object of category
        we want to update and the new name we want to edit"""
        obj.name = name
        self.create(obj)

    def count_items_in_category(self, cid):
        return self.session.\
            query(func.count(Item.id)).\
            filter_by(category_id=cid).\
            scalar()

    def last_items(self):
        last_items = self.session.\
            query(Item,
                  Category.name.label("cname"),
                  Category.id.label("cid"),
                  Item.id,
                  Item.name,
                  Item.description).\
            join(Category, Item.category_id == Category.id).\
            order_by(Item.id.desc()).\
            limit(15)
        return last_items

    def create_item(self, name, description, category_id, user_id):
        item = Item(name=name,
                    description=description,
                    category_id=category_id,
                    user_id=user_id)
        self.create(item)

    def delete(self, obj):
        self.session.delete(obj)

    def update_item(self, obj, name, description, cid):
        obj.name = name
        obj.description = description
        obj.category_id = cid
        self.create(obj)
        return obj

    def create(self, obj):
        self.session.add(obj)
        self.session.commit()

    def category_items(self, cid):

        category = self.get_category(cid)

        items = self.session.\
            query(Item,
                  Category.name.label("cname"),
                  Category.id.label("cid"),
                  Item.id,
                  Item.name,
                  Item.description).\
            filter_by(category_id=cid).\
            join(Category, Item.category_id == Category.id).\
            order_by(Item.id.desc())

        return category, items
    def get_item(self, iid):
        item = self.session.\
            query(Item).\
            filter_by(id=iid).\
            first()
        return item

    def category_item(self, cid, iid):
        category = self.get_category(cid)
        item = self.get_item(iid)
        category_has_item = \
            not (item is None or category is None
                 or item.category_id != category.id)
        return category, item, category_has_item

    @staticmethod
    def record_exist(record):
        return False if (record is None) else True

    @staticmethod
    def records_exist(records):
        return False if (records == []) else True


model = Model()
