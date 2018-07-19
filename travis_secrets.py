def get_arg(self, args, key):
        key = args[key]
        if key.startswith("secret_"):
            if key in self.secret_dict:
                return self.secret_dict[key]
            else:
                self.log("Could not find {} in secret_dict".format(key))
        else:
            return key