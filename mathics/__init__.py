# -*- coding: utf8 -*-

# force utf8 encoding
import sys
#import codecs
#writer = codecs.getwriter("utf-8")
#sys.stdout = writer(sys.stdout)

def get_version():
    version = {}

    import sympy
    import mpmath

    from django.core.exceptions import ImproperlyConfigured

    try:
        import django
        from django.conf import settings
        version['mathics'] = settings.VERSION
        version['django'] = django.get_version()
    except (ImportError, ImproperlyConfigured):
        from mathics import settings
        version['mathics'] = settings.VERSION
    version['sympy'] = sympy.__version__
    version['mpmath'] = mpmath.__version__
    version['python'] = ' '.join([
        'PyPy' if '__pypy__' in sys.builtin_module_names else 'CPython',
        sys.version.split('\n')[0]])
    return version


def get_version_string(is_server, newlines=False):
    version = get_version()
    result = []
    result.append(u"Mathics {0}".format(version['mathics']))
    result.append(u"on {0}".format(version['python']))
    result.append(u"using {0}".format(", ".join([
        "Django {0}".format(version['django']) if (
            'django' in version and is_server) else '',
        "SymPy {0}".format(version['sympy']),
        "mpmath {0}".format(version['mpmath'])
    ])))

    return ("\n" if newlines else " ").join(result)


def print_version(is_server):
    print("\n" + get_version_string(is_server, newlines=True))


def print_license():
    print(u"""
Copyright (C) 2011-2013 The Mathics Team.
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions.
See the documentation for the full license.
""")
