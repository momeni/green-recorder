#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Find the prefix of the current installation, and other useful variables.

Finding the prefix that your program has been installed in can be non-trivial.
This simplifies the process by allowing you to import <packagename>.prefix and
get instant access to the path prefix by calling the function named: prefix().
If you'd like to join this prefix onto a given path, pass it as the first arg.

Example: if [ `./prefix.py` ]; then echo yes; else echo no; fi
Example: x=`./prefix.py`; echo 'prefix: '$x
"""
# Copyright (C) 2010-2012  James Shubin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ('prefix', 'name')
#DEBUG = False

import os
import sys

def prefix(join=None):
    """Returns the prefix that this code was installed into."""
    # constants for this execution
    path = os.path.abspath(__file__)
    #if DEBUG: print 'path: %s' % path
    name = os.path.basename(os.path.dirname(path))
    #if DEBUG: print 'name: %s' % name
    this = os.path.basename(path)
    #if DEBUG: print 'this: %s' % this

    # rule set
    rules = [
        # to match: /usr/lib/python2.5/site-packages/project/prefix.py
        # or: /usr/local/lib/python2.6/dist-packages/project/prefix.py
        lambda x: x == 'lib',
        lambda x: x == ('python%s' % sys.version[:3]),
        lambda x: x in ['site-packages', 'dist-packages'],
        lambda x: x == name,    # 'project'
        lambda x: x == this,    # 'prefix.py'
    ]

    # matching engine
    while len(rules) > 0:
        (path, token) = os.path.split(path)
        #if DEBUG: print 'path: %s, token: %s' % (path, token)
        rule = rules.pop()
        if not rule(token):
            #if DEBUG: print 'rule failed'
            return False

    # usually returns: /usr/ or /usr/local/ (but without slash postfix)
    if join is None:
        return path
    else:
        return os.path.join(path, join)    # add on join if it exists!

def name(pop=[], suffix=None):
    """Returns the name of this particular project. If pop is a list
    containing more than one element, name() will remove those items
    from the path tail before deciding on the project name. If there
    is an element which does not exist in the path tail, then raise.
    If a suffix is specified, then it is removed if found at end."""
    path = os.path.dirname(os.path.abspath(__file__))
    if isinstance(pop, str): pop = [pop]    # force single strings to list
    while len(pop) > 0:
        (path, tail) = os.path.split(path)
        if pop.pop() != tail:
            #if DEBUG: print 'tail: %s' % tail
            raise ValueError('Element doesnʼt match path tail.')

    path = os.path.basename(path)
    if suffix is not None and path.endswith(suffix):
        path = path[0:-len(suffix)]
    return path

if __name__ == '__main__':
    join = None
    if len(sys.argv) > 1:
        join = ' '.join(sys.argv[1:])
    result = prefix(join)
    if result:
        print(result)
    else:
        sys.exit(1)
