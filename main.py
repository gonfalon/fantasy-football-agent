from typing import List

import dotenv
import os
from espn_api.football import League, Player

# Load environment variables into constants
dotenv.load_dotenv()
LEAGUE_ID=int(os.environ.get("LEAGUE_ID"))
LEAGUE_YEAR=int(os.environ.get("LEAGUE_YEAR"))
ESPN_S2=os.environ.get("ESPN_S2")
ESPN_SWID=os.environ.get("ESPN_SWID")
TEAM_NAME=os.environ.get("TEAM_NAME")

def has_position(player: Player) -> bool:
    return True

def main():
    # Pull league data
    league = League(
        league_id=LEAGUE_ID,
        year=LEAGUE_YEAR,
        espn_s2=ESPN_S2,
        swid=ESPN_SWID
    )

    # Find the agent's team
    my_team = None
    for team in league.teams:
        if team.team_name == TEAM_NAME:
            my_team = team
            break
    print(my_team)
    current_roster = my_team.roster

    # Analyze my current roster for substitutions

    # Analyze free agents position by position for waiver pickups

    # Analyze other teams for possible trades

    # Validation check that the recommended moves are valid

    # Notify my human handler of the recommendations via email (or discord? or signal? how would be best/easiest?)

if __name__ == '__main__':
    main()