import dotenv
import os
from espn_api.football import League

dotenv.load_dotenv()

def main():
    league = League(
        league_id=int(os.environ.get("LEAGUE_ID")),
        year=int(os.environ.get("LEAGUE_YEAR")),
        espn_s2=os.environ.get("ESPN_S2"),
        swid=os.environ.get("SWID")
    )
    print(league)

if __name__ == '__main__':
    main()