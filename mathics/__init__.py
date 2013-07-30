# -*- coding: utf8 -*-

# force utf8 encoding
import sys
import codecs
writer = codecs.getwriter("utf-8")
sys.stdout = writer(sys.stdout)


def get_version():
    version = {}

    import sympy
    import sympy.mpmath as mpmath

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
    version['python'] = sys.subversion[0] + " " + sys.version.split('\n')[0]
    return version


def get_version_string(is_server, newlines=False, verbose=True):
    version = get_version()
    result = []
    result.append(u"Mathics %s" % version['mathics'])
    if verbose:
        result.append(u"on %s" % version['python'])
        libs = []
        if 'django' in version and is_server:
            libs.append("Django %s" % version['django'])
        libs += ["SymPy %s" % version['sympy'], "mpmath %s" % version['mpmath']]
        result.append(u"using %s" % ", ".join(libs))
    return ("\n" if newlines else " ").join(result)

def get_license_string(newlines=False, verbose=True):
    result = ["Copyright (C) 2011-2013 The Mathics Team."]
    if verbose:
        result += [
            "This program comes with ABSOLUTELY NO WARRANTY.",
            "This is free software, and you are welcome to redistribute it",
            "under certain conditions.",
            "See the documentation for the full license."]
    return ("\n" if newlines else " ").join(result)


def print_version(is_server):
    print "\n" + get_version_string(is_server, newlines=True)


def print_license():
    print "\n" + get_license_string(newlines=True)

def get_banner_string(is_server, verbose=True):
    return (get_version_string(is_server, newlines=True, verbose=verbose) + "\n"
            + get_license_string(newlines=True, verbose=verbose) + "\n")
