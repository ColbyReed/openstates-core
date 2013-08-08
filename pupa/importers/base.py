import os
import glob
import json
import uuid
import logging
import datetime
from pupa.core import db


def make_id(type_):
    return 'ocd-{0}/{1}'.format(type_, uuid.uuid1())


def collection_for_type(type_):
    if type_ == 'metadata':
        return db.metadata
    elif type_ == 'person':
        return db.people
    elif type_ == 'organization':
        return db.organizations
    elif type_ == 'membership':
        return db.memberships
    elif type_ == 'bill':
        return db.bills
    elif type_ == 'event':
        return db.events
    elif type_ == 'vote':
        return db.votes
    else:
        raise ValueError('unknown type: ' + type_)


def insert_object(obj):
    """ insert a new object into the appropriate collection

    params:
        obj - object to insert

    return:
        database id of new object
    """
    # XXX: check if object already has an id?

    # add updated_at/created_at timestamp
    obj['updated_at'] = obj['created_at'] = datetime.datetime.utcnow()
    obj['_id'] = make_id(obj['_type'])
    collection = collection_for_type(obj['_type'])

    collection.save(obj)
    return obj['_id']


def update_object(old, new):
    """
        update an existing object with a new one, only saving it and
        setting updated_at if something changed

        params:
            old: old object
            new: new object

        returns:
            database_id     id of object in db
            was_updated     whether or not the object was updated
    """
    updated = False

    if old['_type'] != new['_type']:
        raise ValueError('old and new must be of same _type')
    collection = collection_for_type(new['_type'])

    # allow objects to prevent certain fields from being updated
    locked_fields = old.get('_locked_fields', [])

    for key, value in new.items():
        if key in locked_fields:
            continue

        if old.get(key) != value:
            old[key] = value
            updated = True

    if updated:
        old['updated_at'] = datetime.datetime.utcnow()
        collection.save(old)

    return old['_id'], updated


class BaseImporter(object):

    def __init__(self, jurisdiction_id):
        self.jurisdiction_id = jurisdiction_id
        self.collection = collection_for_type(self._type)
        self.results = {'insert': 0, 'update': 0, 'noop': 0}
        self.json_to_db_id = {}
        self.logger = logging.getLogger("pupa")
        self.info = self.logger.info
        self.debug = self.logger.debug
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.critical = self.logger.critical

    def preimport_hook(self, db_obj, obj):
        """
        The preimport_hook allows the importer to modify the object before
        it gets imported. This is sometimes needed to ensure some data won't
        get lost (see people.py)
        """
        pass

    def import_object(self, obj):
        spec = self.get_db_spec(obj)

        db_obj = self.collection.find_one(spec)
        self.preimport_hook(db_obj, obj)

        if db_obj:
            _id, updated = update_object(db_obj, obj)
            self.results['update' if updated else 'noop'] += 1
        else:
            _id = insert_object(obj)
            self.results['insert'] += 1
        return _id

    def dedupe_json_id(self, jid):
        nid = self.duplicates.get(jid, jid)
        if nid != jid:
            return self.dedupe_json_id(nid)
        return jid

    def import_from_json(self, datadir):
        # load all json, mapped by json_id
        raw_objects = {}
        for fname in glob.glob(os.path.join(datadir, self._type + '_*.json')):
            with open(fname) as f:
                data = json.load(f)
                # prepare object from json
                if data['_type'] != 'person':
                    data['jurisdiction_id'] = self.jurisdiction_id
                json_id = data.pop('_id')
                data = self.prepare_object_from_json(data)
                raw_objects[json_id] = data

        # map duplicate ids to first occurance of same object
        duplicates = {}
        items = list(raw_objects.items())
        for i, (json_id, obj) in enumerate(items):
            for json_id2, obj2 in items[i:]:
                if json_id != json_id2 and obj == obj2:
                    duplicates[json_id2] = json_id
        self.duplicates = duplicates

        # now do import, ignoring duplicates
        to_import = sorted([(k, v) for k, v in raw_objects.items()
                            if k not in duplicates],
                           key=lambda i: i[1].get('parent_id', 0))

        for json_id, obj in to_import:
            # parentless objects come first, should mean they are in
            # self.json_to_db_id before their children need them so we can
            # resolve their id
            # XXX: known issue here if there are sub-subcommittees, it'll
            # result in an unresolvable id
            parent_id = obj.get('parent_id')
            if parent_id:
                obj['parent_id'] = self.resolve_json_id(parent_id)

            self.json_to_db_id[json_id] = self.import_object(obj)

        return {self._type: self.results}

    def resolve_json_id(self, json_id):
        """
            Given an id found in scraped JSON, return a DB id for the object.

            params:
                json_id:    id from json

            returns:
                database id

            raises:
                ValueError if id couldn't be resolved
        """
        if not json_id:
            return None

        json_id = self.dedupe_json_id(json_id)

        # make sure this sort of looks like a UUID
        if len(json_id) != 36:
            raise ValueError('cannot resolve non-uuid: {0}'.format(json_id))

        try:
            return self.json_to_db_id[json_id]
        except KeyError:
            raise ValueError('cannot resolve id: {0}'.format(json_id))

    def prepare_object_from_json(self, obj):
        # no-op by default
        return obj
