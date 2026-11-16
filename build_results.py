"""Build the weekly NFL yardage leaders for the Pick Three league sheet.

Writes two small CSV files that the Google Sheet reads with IMPORTDATA:
  results_<season>.csv   week, place, and the top 12 passers, rushers and
                         receivers. Always 18 x 12 rows so each row lines up
                         with the sheet; weeks not yet finished are blank.
  players_<season>.csv   every player with yards this season (spell check).

Standard library only. Source: the public nflverse data files.
"""
import csv, io, sys, urllib.request

SEASON = 2026
WEEKS, PLACES = 18, 12
STATS = ("https://github.com/nflverse/nflverse-data/releases/download/"
         f"stats_player/stats_player_week_{SEASON}.csv")
GAMES = "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
CATS = ("passing_yards", "rushing_yards", "receiving_yards")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pick3-results"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode("utf-8"))))


def finished_weeks(games):
    """Regular-season weeks in which every game has a final score."""
    total, done = {}, {}
    for g in games:
        if g["season"] != str(SEASON) or g["game_type"] != "REG":
            continue
        w = int(g["week"])
        total[w] = total.get(w, 0) + 1
        if g["result"] not in ("", "NA"):
            done[w] = done.get(w, 0) + 1
    return sorted(w for w in total if done.get(w) == total[w])


def leaders(stats, weeks):
    top = {(w, c): [] for w in weeks for c in CATS}
    players = set()
    for r in stats:
        if r["season_type"] != "REG":
            continue
        w = int(r["week"])
        for c in CATS:
            y = float(r[c] or 0)
            if y <= 0:
                continue
            players.add(r["player_display_name"])
            if (w, c) in top:
                top[(w, c)].append((r["player_display_name"], int(y)))
    for k in top:                      # yards high to low, then name
        top[k] = sorted(top[k], key=lambda t: (-t[1], t[0]))[:PLACES]
    return top, sorted(players)


def main():
    weeks = finished_weeks(fetch(GAMES))
    top, players = leaders(fetch(STATS), weeks)
    if not weeks or not players:
        sys.exit("no finished weeks or no players found: leaving files untouched")
    with open(f"results_{SEASON}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["week", "place", "pass_player", "pass_yds", "rush_player",
                    "rush_yds", "rec_player", "rec_yds"])
        for wk in range(1, WEEKS + 1):
            for p in range(PLACES):
                row = [wk, p + 1]
                for c in CATS:
                    got = top.get((wk, c), [])
                    row += list(got[p]) if p < len(got) else ["", ""]
                w.writerow(row)
    with open(f"players_{SEASON}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["player"])
        w.writerows([p] for p in players)
    print(f"finished weeks: {weeks}; players: {len(players)}")


if __name__ == "__main__":
    main()
