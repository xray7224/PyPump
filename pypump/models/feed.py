##
# Copyright (C) 2013 Jessica T. (Tsyesika) <xray7224@googlemail.com>
# 
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. 
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##

from pypump.compatability import *
from pypump.exception import PyPumpException 
from pypump.models import AbstractModel

class InfiniteFeed(object):
    
    previous = None

    def __init__(self, feed):
        self.feed = feed

    def __iter__(self):
        return self

    def next(self):
        if self.previous is None:
            # first iteration
            data = self.feed._request(count=1)
        else:
            data = self.feed._request(count=1, before=self.previous)

        data = data["items"]
        if not data:
            # we're done
            raise StopIteration
        
        obj = getattr(self.feed._pump, self.feed.OBJECT_TYPES)
        obj = obj.unserialize(data[0])
        self.previous = obj.id
        return obj

@implement_to_string
class Feed(AbstractModel):

    _count = None
    _offset = None
    actor = None
    author = actor

    _ENDPOINT = None
    @property
    def ENDPOINT(self):
        if self._ENDPOINT is None:
            raise NotImplemented("Definition of the ENDPOINT must be done by subclass")
        return self._ENDPOINT

    @property
    def major(self):
        endpoint = self.ENDPOINT
        if not endpoint.endswith("/"):
            endpoint += "/"
        endpoint += "major"
        return self.__class__(username=self.actor, endpoint=endpoint)

    @property
    def minor(self):
        endpoint = self.ENDPOINT
        if not endpoint.endswith("/"):
            endpoint += "/"
        endpoint += "minor"
        return self.__class__(username=self.actor, endpoint=endpoint)

    def __init__(self, username=None, endpoint=None):
        if endpoint is not None:
            self._ENDPOINT = endpoint
        
        if isinstance(username, self._pump.Person):
            self.actor = username
            return

        self.actor = self._pump.Person(username)        

    def __getitem__(self, key):
        """ Adds Feed[<feed>] """
        if isinstance(key, slice):
            return self.__getslice__(key)
        count = 1
        offset = key
        data = self._request(offset=offset, count=count)
        data = self.unserialize(data)
        return data[0]

    def __getslice__(self, s, e=None):
        """ Grab multiple items from feed """
        if type(s) is not slice:
            s = slice(s,e)

        if s.start and s.stop:
            count = s.stop - s.start
            offset = s.start
        elif s.stop:
            count = s.stop
            offset = None
        elif s.start:
            offset = s.start
            count = None

        data = self._request(offset=offset, count=count)
        data = self.unserialize(data)

        if s.step:
            return data[::s.step]
        else:
            return data

    def __iter__(self):
        """ Produces an iterator """
        return InfiniteFeed(self) 
    
    def __repr__(self):
        if self.author:
            return "<{type}: {actor}>".format(
                    actor=self.actor,
                    type=self.TYPE,
                    )
        else:
            return "<{type}>".format(type=self.TYPE)
    
    def __str__(self):
        return str(repr(self))

    def _request(self, offset=None, count=None, since=None, before=None):
        """ Makes a request """
        param = dict()

        if count is not None:
            param["count"] = count

        if offset is not None:
            param["offset"] = offset

        if since is not None:
            param["since"] = before
        elif before is not None:
            param["before"] = before

        if self.actor is None:
            # oh dear, we gotta raise an error
            raise PyPumpException("No actor defined on {feed}".format(feed=self))

        data = self._pump.request(self.ENDPOINT, params=param)

        return data

    @classmethod
    def unserialize(cls, data, user=None):
        """ Produce a List from JOSN data """
        if type(data) == list:
            items = data
        elif type(data) == dict:
            items = data["items"]
        else:
            raise Exception("Unknown type: {type} ('{data}')".format(
                    type=type(data),
                    data=data
                    ))

        unserialized_items = list()

        for v in items:
            # do we know about it?
            obj_type = cls.OBJECT_TYPES

            # todo: make less hacky
            try:
                obj = getattr(cls._pump, obj_type)
            except AttributeError:
                continue # what is this stange type of which you are?
            
            try:
                real_obj = obj.unserialize(v)
                if real_obj is not None:
                    unserialized_items.append(real_obj)
            except TypeError:
                pass

        return unserialized_items
