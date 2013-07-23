import os
import json
import datetime
from pupa.core import db
from larvae.utils import DatetimeValidator


def import_jurisdiction(org_importer, jurisdiction):
    metadata = jurisdiction.get_metadata()

    metadata['_type'] = 'metadata'
    metadata['_id'] = jurisdiction.jurisdiction_id
    metadata['latest_update'] = datetime.datetime.utcnow()

    # validate metadata
    validator = DatetimeValidator()
    with open(os.path.join(os.path.dirname(__file__),
                           '../schemas/metadata.json')) as f:
        metadata_schema = json.load(f)
    try:
        validator.validate(metadata, metadata_schema)
    except ValueError as ve:
        raise ve

    db.metadata.save(metadata)

    # create organization
    org = {'_type': 'organization',
           'classification': 'jurisdiction',
           'parent_id': None,
           'jurisdiction_id': jurisdiction.jurisdiction_id,
           'name': metadata['name']
          }
    if 'other_names' in metadata:
        org['other_names'] = metadata['other_names']
    if 'parent_id' in metadata:
        org['parent_id'] = metadata['parent_id']

    org_importer.import_object(org)

    # create parties
    for party in metadata['parties']:
        org = {'_type': 'organization',
               'classification': 'party',
               'name': party['name'],
               'parent_id': None }
        org_importer.import_object(org)
