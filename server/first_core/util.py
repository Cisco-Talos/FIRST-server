#-------------------------------------------------------------------------------
#
#   FIRST Utility and Helper Functions
#   Copyright (C) 2017  Angel M. Villegas
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#-------------------------------------------------------------------------------


def make_id(flags, metadata=0, engine=0):
    '''Creates an unique ID for client use.

     Args:
        flag (:obj:`int`): Value between 0 and 255.
                            MSB set when ID is from an engine.
        metadata (:obj:`int`, optional): The Metadata model ID
        engine (:obj:`int`, optional): The Engine model ID

    Returns:
        string: A 26 byte hex string
    '''
    data = [flags, metadata, engine]
    if (None in data) or (not all([type(x) in [int, long] for x in data])):
        return None

    if ((engine > (2**32 - 1)) or (metadata > (2**64 - 1))
        or (flags > (2**8 - 1))):
        return None

    return '{:02x}{:08x}{:016x}'.format(flags, engine, metadata)


def parse_id(_id):
    if len(_id) != 26:
        return (None, None, None)

    _id = int(_id, 16)
    flag = _id >> (8 * 12)
    engine_data = (_id >> (8 * 8)) & (0xFFFFFFFF)
    metadata_id = _id & 0xFFFFFFFFFFFFFFFF

    return (flag, engine_data, metadata_id)

def separate_metadata(ids):
    '''Returns parsed IDs for user and engine generated metadata.

     Args:
        ids (:obj:`list`): List of 26 hex strings
        metadata (:obj:`int`, optional): The Metadata model ID
        engine (:obj:`int`, optional): The Engine model ID

    Returns:
        tuple: Index 0 contains user created metadata IDs
                Index 1 contains engine created metadata details
    '''
    #   ID: Flag Byte | Engine 4 bytes | Metadata 8 bytes = 13 bytes
    #       26 ASCII characters
    #   If Flag is set then more processing is needed and it is not
    #   metadata created by the user
    user_metadata = []
    engine_metadata = []
    for x in ids:
        flag, engine_data, metadata_id = parse_id(x)
        if None in [flag, engine_data, metadata_id]:
            continue

        if not flag:
            user_metadata.append(metadata_id)
        else:
            engine_metadata.append((flag, engine_data, metadata_id))

    return (user_metadata, engine_metadata)

def is_user_metadata(_id):
    details = parse_id(_id)
    if None in details:
        return False

    if not details[0]:
        return True

    return False

def is_engine_metadata(_id):
    details = parse_id(_id)
    if None in details:
        return False

    if details[0]:
        return True

    return False
