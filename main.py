from typing import List
import dotenv
import os
from espn_api.football import League, Player
from ollama import Client, ChatResponse

# Load environment variables into constants
dotenv.load_dotenv()
LEAGUE_ID=int(os.environ.get("LEAGUE_ID"))
LEAGUE_YEAR=int(os.environ.get("LEAGUE_YEAR"))
ESPN_S2=os.environ.get("ESPN_S2")
ESPN_SWID=os.environ.get("ESPN_SWID")
TEAM_NAME=os.environ.get("TEAM_NAME")

# import systemprompt.txt into a variable
with open('prompts/systemprompt.txt', 'r') as f:
    system_prompt = f.read()

# import substitutionanalysis.txt into a varialbe
with open('prompts/substitutionanalysis.txt', 'r') as f:
    substitution_analysis = f.read()

def has_position(player: Player, position: str) -> bool:
    return player.position.upper() == position.upper()

def pretty_print_players(players: List[Player], league: League) -> str:
    """Formats a list of players into a pretty-printed string with stats."""
    if not players:
        return "None"

    # Create a header for our table
    header = f"{'Name':<20} | {'POS':<5} | {'Team':<5} | {'Total':<7} | {'Proj':<7} | {'Avg':<7}"
    lines = [header, '-' * len(header)]

    # Add each player as a row
    for p in players:
        avg_points = p.total_points / league.current_week if league.current_week > 0 else 0
        line = f"{p.name:<20} | {p.position:<5} | {p.proTeam:<5} | {p.total_points:<7.2f} | {p.projected_total_points:<7.2f} | {avg_points:<7.2f}"
        lines.append(line)

    return '\n'.join(lines)

def main():

    ollama = Client()

    # Pull league data
    league = League(
        league_id=LEAGUE_ID,
        year=LEAGUE_YEAR,
        espn_s2=ESPN_S2,
        swid=ESPN_SWID
    )
    print(league.free_agents(size=1000, position="QB"))

    # Find the agent's team
    my_team = None
    for team in league.teams:
        if team.team_name == TEAM_NAME:
            my_team = team
            break
    print(my_team)
    current_roster = my_team.roster

    # Analyze my current roster for substitutions
    for position in ["QB"]: #, "RB", "WR", "TE", "FLEX", "D/ST", "K"]:
        starters = [player for player in my_team.roster if player.lineupSlot.upper() == position.upper()]
        eligible = [player for player in my_team.roster if position.upper() in player.eligibleSlots]
        
        starters_str = pretty_print_players(starters, league)
        eligible_str = pretty_print_players(eligible, league)

        substitution_analysis_prompt = substitution_analysis.format(
            position=position,
            starters=starters_str,
            eligible=eligible_str
        )
        print(substitution_analysis_prompt)
        print("Asking GPT-OSS for recommendations...")
        recommendation : ChatResponse = ollama.chat(
            model="gpt-oss:20b",
            think=True,
            messages=[{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": substitution_analysis_prompt
            }]
        )
        print(recommendation.message.content)
        save_rec(recommendation)

    # Analyze free agents position by position for waiver pickups
    for position in ["QB", "RB", "WR", "TE", "FLEX", "D/ST", "K"]:
        free_agents = league.free_agents(size=1000, position=position)
        free_agents_str = pretty_print_players(free_agents, league)

    # Analyze other teams for possible trades

    # Validation check that the recommended moves are valid

    # Notify my human handler of the recommendations via email (or discord? or signal? how would be best/easiest?)


def save_rec(recommendation):
    # Save the recommendation to a log file
    if not os.path.exists('output'):
        os.makedirs('output')
    with open('output/recommendations.log', 'a') as logfile:
        logfile.append(recommendation.message.content)


if __name__ == '__main__':
    main()