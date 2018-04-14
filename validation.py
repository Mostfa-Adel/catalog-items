class Validator:
    """ class for validate a form """
    # get form errors return a dictionary of list of form errors messages
    # you can add new validation types just by make the function
    # of new validation as required function
    # and add an if statement in valid_form function as required been added
    def __init__(self):
        self._errors_dict = {}

    def get_form_errors(self):
        return self._errors_dict

    def valid_form(self):
        for (key, val) in self._errors_dict.items():
            if val != []:
                return False
        return True

    def validate(self, field, field_name, rules_list=['required']):
        self._errors_dict[field_name] = []
        for rule in rules_list:
            if rule == "required":
                self.required(field, field_name)

    def required(self, field, field_name):
        if field == "":
            self._errors_dict[field_name].\
                append("%s field is required" % field_name)
