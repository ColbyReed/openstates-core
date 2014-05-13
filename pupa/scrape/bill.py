from .base import BaseModel, SourceMixin, AssociatedLinkMixin, make_psuedo_id, cleanup_list
from .schemas.bill import schema


class Action(dict):

    def add_related_entity(self, name, entity_type, entity_id=None):
        ent = {
            'name': name,
            'entity_type': entity_type,
            entity_type + '_id': entity_id,
        }
        self['related_entities'].append(ent)
        return ent


class Bill(SourceMixin, AssociatedLinkMixin, BaseModel):
    """
    An Open Civic Data bill.
    """

    _type = 'bill'
    _schema = schema

    def __init__(self, name, session, title, chamber=None, from_organization=None,
                 classification=None):
        super(Bill, self).__init__()

        self.name = name
        self.session = session
        self.title = title
        self.classification = cleanup_list(classification, ['bill'])

        if from_organization and chamber:
            raise ValueError('cannot specify both chamber and from_organization')
        elif chamber:
            self.from_organization = make_psuedo_id(classification='legislature', chamber=chamber)
        elif from_organization:
            self.from_organization = from_organization
        else:
            # neither specified
            self.from_organization = make_psuedo_id(classification='legislature')

        self.actions = []
        self.other_names = []
        self.other_titles = []
        self.documents = []
        self.related_bills = []
        self.sponsors = []
        self.subject = []
        self.summaries = []
        self.versions = []

    def add_action(self, description, actor, date, classification=None,
                   related_entities=None):
        action = Action(description=description, actor=actor, date=date,
                        classification=cleanup_list(classification, []), related_entities=[])
        self.actions.append(action)
        return action

    def add_related_bill(self, name, session, relation_type):
        self.related_bills.append({
            "name": name,
            "session": session,
            "relation_type": relation_type  # enum
        })

    def add_sponsor(self, name, classification, entity_type, primary,
                    chamber=None, entity_id=None):
        sp = {
            "name": name,
            "classification": classification,
            "entity_type": entity_type,
            "primary": primary,
            entity_type + '_id': entity_id,
        }
        self.sponsors.append(sp)

    def add_subject(self, subject):
        self.subject.append(subject)

    def add_summary(self, text, note):
        self.summaries.append({"note": note, "text": text})

    def add_title(self, text, note=''):
        self.other_titles.append({"note": note, "text": text})

    def add_name(self, name, note=''):
        self.other_names.append({"note": note, "name": name})

    def add_document_link(self, name, url, date='', type='', mimetype='', on_duplicate='error'):
        return self._add_associated_link(collection='documents', name=name, url=url, date=date,
                                         type=type, mimetype=mimetype, on_duplicate=on_duplicate)

    def add_version_link(self, name, url, date='', type='', mimetype='', on_duplicate='error'):
        return self._add_associated_link(collection='versions', name=name, url=url, date=date,
                                         type=type, mimetype=mimetype, on_duplicate=on_duplicate)

    def __str__(self):
        return self.name + ' in ' + self.session
    __unicode__ = __str__
