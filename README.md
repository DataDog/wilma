<h1 align="center">Wilma</h1>
<h3 align="center">Smarter-than-caveman debugging</h3>


## Who is Wilma?

Wilma is a Python debugging tool intended to solve some of the issues that come
with the traditional practice of _print-statement debugging_ (also known as
[Caveman Debugging][caveman]).


## What are the issues?

> "The most effective debugging tool is still careful thought, coupled with
> judiciously placed print statements."
>
> — Brian Kernighan, "Unix for Beginners" (1979)

One problem with this approach is that it requires changing the source code to
add new print statements. Most of them would probably need to be removed before
the code goes to production, and there is always a chance that some might be go
unnoticed and forgotten. Furthermore, it is not easy to toggle them on or off
while debugging, as they tend to be scattered across multiple sources.


## How Wilma solves them

Wilma lets you define print statements in a separate configuration file, which
are then _injected_ into the bytecode at runtime. This means that there is no
longer the need to make changes to source files (not only that, but one can
easily add print statement to third-party libraries too!). Consequently, there
is no risk of forgetting print statements in sources, and switching them off is
as easy as commenting them out in just a single place!


## Example

Suppose that we have a function that takes a single argument, e.g.

~~~ python
# File: test.py
def foo(secret):
    print("I'm not telling you the secret!")
    return None

foo("Wilma rox!")
~~~

There is no way of knowing what was passed to the function when it is called by
just looking at its output:

~~~
$ python -m test
I'm not telling you the secret!
~~~

So we can use Wilma to inject a print statement at the beginning of line 4 that
prints the value of the `secret` argument:

~~~ toml
# File: wilma.toml
[probes]
"test.py:4" = "print('The secret is: ', secret)"
~~~

If we now run the same script through Wilma, this time we get:

~~~
$ wilma python -m test
I'm not telling you the secret!
The secret is: Wilma rox!
~~~

By default, Wilma looks for the file `wilma.toml` in the current working
directory. You can specify a custom Wilma file with the `-c/--config` option.

> **NOTE** Wilma should be installed within the same environment of the target
> application to work properly. For examole, you may want to list Wilma amongst
> the developent dependencies of your project.


## Tools

Wilma comes with a set of useful tools to quickly perform debug operations. For
example, to change the value of the `secret` local variable, you can use the
following configuration

~~~ toml
# File: wilma.toml
[probes]
"test.py:3" = """
with wilma.locals() as ls:
    ls["secret"] = "new secret"
"""
"test.py:4" = "print('The secret is: ', secret)"
~~~

When you run the `test` module you should now see `new secret` instead of the
original value.

> The `wilma` module is imported automatically, so there is no need to add it
> explicitly to the imports.


[caveman]: https://medium.com/@firhathidayat/the-caveman-debugging-ab8f7151415f
