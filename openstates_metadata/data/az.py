from ..models import State, Chamber

AZ = State(
    name="Arizona",
    abbr="AZ",
    capital="Phoenix",
    capital_tz="America/Denver",
    fips="04",
    unicameral=False,
    legislature_name="Arizona State Legislature",
    lower=Chamber(
        chamber_type="lower",
        name="House",
        num_seats=60,
        seats={
            "1": 2,
            "2": 2,
            "3": 2,
            "4": 2,
            "5": 2,
            "6": 2,
            "7": 2,
            "8": 2,
            "9": 2,
            "10": 2,
            "11": 2,
            "12": 2,
            "13": 2,
            "14": 2,
            "15": 2,
            "16": 2,
            "17": 2,
            "18": 2,
            "19": 2,
            "20": 2,
            "21": 2,
            "22": 2,
            "23": 2,
            "24": 2,
            "25": 2,
            "26": 2,
            "27": 2,
            "28": 2,
            "29": 2,
            "30": 2,
        },
        division_ids=None,
        title="Representative",
    ),
    upper=Chamber(
        chamber_type="upper",
        name="Senate",
        num_seats=30,
        seats=None,
        division_ids=None,
        title="Senator",
    ),
)
