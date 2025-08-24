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
ESPN_SW_ID=os.environ.get("ESPN_SW_ID")
TEAM_NAME=os.environ.get("TEAM_NAME")
OLLAMA_URL=os.environ.get("OLLAMA_URL")
OLLAMA_MODEL=os.environ.get("OLLAMA_MODEL")

POSITION_LIST=["QB", "RB", "WR", "TE", "FLEX", "D/ST", "K"]

# import system_prompt.txt into a variable
with open('prompts/system_prompt.txt', 'r') as f:
    system_prompt = f.read()

# import substitution_analysis.txt into a variable
with open('prompts/substitution_analysis.txt', 'r') as f:
    substitution_analysis = f.read()


# import substitution_analysis.txt into a variable
with open('prompts/free_agent_search.txt', 'r') as f:
    free_agent_search = f.read()

    # import substitution_analysis.txt into a variable
with open('prompts/trade_eval.txt', 'r') as f:
    trade_eval = f.read()

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

    ollama = Client(host=OLLAMA_URL)

    # Pull league data
    league = League(
        league_id=LEAGUE_ID,
        year=LEAGUE_YEAR,
        espn_s2=ESPN_S2,
        swid=ESPN_SW_ID
    )

    # Find the agent's team
    my_team = None
    for team in league.teams:
        if team.team_name == TEAM_NAME:
            my_team = team
            break
    print(my_team)

    # Analyze my current roster for substitutions
    for position in POSITION_LIST: #, "RB", "WR", "TE", "FLEX", "D/ST", "K"]:
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
            model=OLLAMA_MODEL,
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
    for position in POSITION_LIST:
        eligible = [player for player in my_team.roster if position.upper() in player.eligibleSlots]
        eligible_str = pretty_print_players(eligible, league)
        free_agents = league.free_agents(size=1000, position=position)
        free_agents_str = pretty_print_players(free_agents, league)
        free_agent_search_prompt = free_agent_search.format(my_roster=eligible_str, free_agents=free_agents_str, position=position)
        print("Asking GPT-OSS for recommendations...")
        recommendation: ChatResponse = ollama.chat(
            model=OLLAMA_MODEL,
            think=True,
            messages=[{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": free_agent_search_prompt
            }]
        )
        print(recommendation.message.content)
        save_rec(recommendation)

    # Analyze other teams for possible trades
    my_roster_str = pretty_print_players(my_team.roster, league)
    for team in league.teams:
        if team.team_name == TEAM_NAME:
            continue

        opponent_roster_str = pretty_print_players(team.roster, league)
        trade_eval_prompt = trade_eval.format(
            my_team_name=TEAM_NAME,
            opponent_team_name=team.team_name,
            my_roster=my_roster_str,
            opponent_roster=opponent_roster_str
        )
        recommendation: ChatResponse = ollama.chat(
            model=OLLAMA_MODEL,
            think=True,
            messages=[{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": trade_eval_prompt
            }]
        )
        print(recommendation.message.content)
        save_rec(recommendation)

    # Notify my human handler of the recommendations via email (or discord? or signal? how would be best/easiest?)


def save_rec(recommendation: ChatResponse):
    # Save the recommendation to a log file
    if not os.path.exists('output'):
        os.makedirs('output')
    with open('output/recommendations.md', 'a') as logfile:
        logfile.write(recommendation.message.content)


if __name__ == '__main__':
    main()