SECRET = "I'm an imported secret!"


def foo():
    print("I'm not telling you the imported secret!")
    return None


class Foo:
    __secret__ = "I'm an imported class secret!"

    def bar(self):
        print("I'm not telling you the imported class secret!")
        return None
