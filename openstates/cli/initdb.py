from openstates_metadata import STATES_BY_ABBR
from ..utils.django import init_django


def create_division(division_id, name):
    from ..data.models import Division

    return Division.objects.get_or_create(
        id=division_id, defaults=dict(name=name, country="us")
    )[0]


def create_chamber(juris, parent, chamber):
    from ..data.models import Organization, Post

    if chamber.chamber_type != "unicameral":
        post_parent, created = Organization.objects.get_or_create(
            id=chamber.organization_id,
            classification=chamber.chamber_type,
            parent_id=parent.id,
            jurisdiction_id=juris.id,
            name=chamber.name,
        )
    else:
        # parent is unicameral org
        post_parent = parent

    # create divisions and posts
    for district in chamber.districts:
        post_div = create_division(
            district.division_id, f"{juris.name} {chamber.name} {district.name}"
        )
        Post.objects.get_or_create(
            label=district.name,
            organization=post_parent,
            division=post_div,
            # TODO: allow changing role & max_memberships
            defaults=dict(role=chamber.title, maximum_memberships=district.num_seats),
        )


def create_full_jurisdiction(state):
    from ..data.models import Jurisdiction, Organization

    div = create_division(state.division_id, state.name)
    juris = Jurisdiction.objects.create(
        id=state.jurisdiction_id, name=state.name, url=state.url, division=div
    )
    leg = Organization.objects.create(
        id=state.legislature_organization_id,
        name=state.legislature_name,
        classification="legislature",
        jurisdiction=juris,
    )
    # create executive
    Organization.objects.create(
        id=state.executive_organization_id,
        name=state.executive_name,
        classification="executive",
        jurisdiction=juris,
    )

    if state.unicameral:
        create_chamber(juris, leg, state.legislature)
    else:
        create_chamber(juris, leg, state.lower)
        create_chamber(juris, leg, state.upper)


def load_jurisdictions():
    for name, state in STATES_BY_ABBR.items():
        print("creating", name)
        create_full_jurisdiction(state)


def main():
    init_django()
    load_jurisdictions()
