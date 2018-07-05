def get_arg(args, key):
        key = args[key]
        if key.startswith("secret_"):
            if key in secrets.secret_dict:
                return secrets.secret_dict[key]
            else:
                raise KeyError("Could not find {} in secret_dict".format(key))
        else:
            return key

def get_arg_list(args, key):
    arg_list = []
    for key in self.split_device_list(args[key]):
        if type(key) is str and key.startswith("secret_"):
            if key in secrets.secret_dict:
                arg_list.append(secrets.secret_dict[key])
            else:
                raise KeyError("Could not find {} in secret_dict".format(key))
        else:
            arg_list.append(key)
    return arg_list