import sub.importme as im


def foo(secret):
    print("I'm not telling you the secret!")
    return None


class Foo:
    __secret__ = "I'm a class secret!"

    def bar(self):
        print("I'm not telling you the class secret!")
        return None


foo("Wilma rox!")
Foo().bar()


im.foo()
im.Foo().bar()
