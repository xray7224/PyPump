##
# Copyright (C) 2015 Jessica T. (Tsyesika) <xray7224@googlemail.com>
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

import logging
from pypump.models import (PumpObject, Likeable, Shareable, Commentable,
                           Deleteable, Uploadable, Mapper)

_log = logging.getLogger(__name__)


class MediaObject(PumpObject, Likeable, Shareable, Commentable, Deleteable, Uploadable):

    object_type = 'dummy'
    _ignore_attr = ["summary"]
    _mapping = {
        "stream": "stream",
        "license": "license",
        "embed_code": "embedCode",
    }

    def __init__(self, display_name=None, content=None, license=None, **kwargs):
        super(MediaObject, self).__init__(**kwargs)

        self.display_name = display_name
        self.content = content
        self.license = license

    def __repr__(self):
        return "<{type} by {webfinger}>".format(
            type=self.object_type.capitalize(),
            webfinger=getattr(self.author, 'webfinger', 'unknown')
        )

    def __unicode__(self):
        return u"{type} by {webfinger}".format(
            type=self.object_type,
            webfinger=getattr(self.author, 'webfinger', 'unknown')
        )


class Video(MediaObject):

    object_type = 'video'


class Audio(MediaObject):

    object_type = 'audio'


class ImageContainer(object):
    """ Container that holds information about an image.

    :param url: URL to image file on the pump.io server.
    :param width: Width of the image.
    :param height: Height of the image.
    """
    def __init__(self, url, width, height):
        self.url = url
        self.width = width
        self.height = height

    def __repr__(self):
        return "<Image {width}x{height}>".format(
            width=self.width,
            height=self.height
        )


class Image(MediaObject):
    """ This object represents a pump.io **image**,
    images are used to post image content with optional text (or html) messages
    to the pump.io network.

    :param content: (optional) Image text content.
    :param display_name: (optional) Image title.

    Example:
        >>> myimage = pump.Image(display_name='Happy Caturday!')
        >>> myimage.from_file('/path/to/kitteh.png')
    """

    object_type = 'image'
    _ignore_attr = ["summary", "image"]
    _mapping = {
        "thumbnail": "image",
        "original": "fullImage",
        "license": "license",
    }

    def unserialize(self, data):

        def get_fileurl(data):
            if data.get("pump_io", {}).get("proxyURL"):
                return data["pump_io"]["proxyURL"]
            else:
                return data["url"]

        if "fullImage" in data:
            full_image = data["fullImage"]
            self.original = ImageContainer(
                url=get_fileurl(full_image),
                height=full_image.get("height"),
                width=full_image.get("width")
            )

        if "image" in data:
            save_point = "original" if not hasattr(self, "original") else "thumbnail"
            thumbnail = data["image"]

            setattr(self, save_point, ImageContainer(
                url=get_fileurl(thumbnail),
                height=thumbnail.get("height"),
                width=thumbnail.get("width")
            ))
        Mapper(pypump=self._pump).parse_map(self, data=data)
        self._add_links(data)

        return self