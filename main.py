#!/usr/bin/env python3
"""Loading Screen Gold: A Tip in 200 Characters.

Competition: u-ricoxyz-loading-screen-gold-a-tip-in-200-characters-2b1df270
("Loading Screen Gold: A Tip in 200 Characters", make.fun).

The task: write ONE loading-screen tip, at most 200 characters, for stressed
developers AND AI coding agents at once -- sharp and funny enough to land
mid-build. A house judge compares entries two at a time, weighing, most
important first:

  1. Is a loading-screen tip for stressed developers and AI coding agents
     (not a slogan, a status message, or a joke about something else).
  2. Earns a real laugh from someone tired at a keyboard, through a turn or
     a punchline rather than a pun that only groans.
  3. Lands in a glance: a single line, every word working.
  4. Speaks to a stressed developer and to an AI coding agent at once, so
     both feel the joke is about them.
  5. Feels fresh, not a rerun of the usual coffee, deadline or compile jokes.

The gate: /output/entry.txt must be UTF-8 text of 1 to 200 characters, not
only white space.

How this program works
----------------------
It drafts several candidates, scores each one against the judge's five
criteria in the judge's own priority order, picks the highest-scoring line
(ties break to the shorter text), writes it to /output/entry.txt, and prints
it to stdout. Everything is fixed data and arithmetic: no network, no
randomness, no clock. Run it twice and the output is byte-identical.

Round 2 fix (why round 1 exited 1 in the grader): the grader runs the
program from a READ-ONLY /bot directory, and round 1 unconditionally wrote
a second copy of the entry next to the program (entry.txt beside main.py).
That write raised PermissionError after /output/entry.txt was already
written correctly, so the process still exited 1. This version writes ONLY
to /output/entry.txt (falling back to ./entry.txt when /output is not
writable, e.g. a local run) and never writes beside the program except as
a best-effort copy guarded by try/except, which can never fail the run.
"""

import os
import sys

# ---------------------------------------------------------------------------
# The candidates. Every line is a single line of at most 200 characters.
# The two subjective criteria (2: the laugh, 5: freshness) are scored by hand
# below, with the reason written next to each score, because only a reader
# can judge a punchline. The other three criteria are computed from the text.
# ---------------------------------------------------------------------------
CANDIDATES = [
    "Tip: your agent finished in 12 seconds. You will spend 12 minutes "
    "deciding if you trust it. That gap is the job now.",
    "Loading... your agent already fixed the bug, broke two features, and "
    "is now waiting for you to notice. Breathe. Read the diff first.",
    "Tip: the build is not stuck. Your agent is rehearsing its apology "
    "for the file it is about to rename without telling you.",
    "Loading... while you wait, your agent is quietly deleting the comment "
    "that said 'do not touch this'. It touched it. It was right.",
    "Tip: if the agent looks done and you feel useless, congratulations - "
    "you have been promoted to the person who reads the diff.",
    "Your agent just renamed a variable across 400 files and feels great "
    "about it. Your only job left is to ask why, out loud, slowly.",
    "Loading... your agent is 400 files deep and still confident. You are "
    "one prompt away from asking it to explain itself. Breathe.",
    "Tip: your agent finished in 12 seconds. You will spend 12 minutes "
    "deciding if you trust it \u2014 then approve it unread anyway.",
]

# Hand scores for the two subjective criteria, 0-5, with the reason.
# Criterion 2 (the laugh): does the line turn, with a punchline that lands
# on a tired reader, instead of a pun that only groans?
# Criterion 5 (freshness): is the angle new, not coffee / deadline /
# compile, and not another well-worn developer trope?
LAUGH = {
    0: (4, "The punchline reframes the whole job: the agent is instant, the "
           "human's work is now the doubt. But 'That gap is the job now' is "
           "a statement, not a second beat -- the laugh lands on "
           "recognition and stops there, where the best lines turn again."),
    1: (4, "'Broke two features, and is now waiting for you to notice' is a "
           "real turn -- the agent as a guilty coworker -- but the laugh "
           "peaks at the middle, not at the end."),
    2: (3, "'Rehearsing its apology' is a nice image, but the line explains "
           "its own joke instead of landing it."),
    3: (4, "'It touched it. It was right.' is a tight two-beat punchline, "
           "but it leans on the familiar 'do not touch this' comment trope."),
    4: (4, "'Promoted to the person who reads the diff' is a strong "
           "punchline, but it needs the reader to feel useless first, which "
           "is a slower setup."),
    5: (3, "A funny picture, but 'ask why, out loud, slowly' is a shrug, "
           "not a punchline."),
    6: (3, "'One prompt away from asking it to explain itself' is wry, not "
           "a laugh; the line ends on 'Breathe', which is advice, not a "
           "turn."),
    7: (5, "'Then approve it unread anyway' is the second turn the others "
           "lack: first the doubt, then the confession that the doubt was "
           "theatre. Every tired developer has done exactly this, and the "
           "agent is the straight man the whole way through."),
}
FRESHNESS = {
    0: (5, "Nobody's loading screen has joked about the trust gap: the "
           "agent's speed versus the human's verification time. No coffee, "
           "no deadline, no compile, no 'it works on my machine'."),
    1: (4, "The agent breaking things while fixing them is a current, "
           "lived complaint, not a recycled joke -- though 'read the diff' "
           "is becoming the standard moral of the story."),
    2: (4, "An agent apologising in advance is a new angle, but renaming "
           "files unannounced is already a common agent gripe."),
    3: (3, "The 'do not touch this' comment is a classic developer trope; "
           "the agent angle refreshes it, but the setup is borrowed."),
    4: (4, "The promotion-to-diff-reader framing is new, though 'the agent "
           "did it all and I am useless' is a familiar feeling."),
    5: (3, "Mass renames are a known agent mishap; the joke is a variation "
           "on it, not a new angle."),
    6: (3, "An overconfident agent deep in the codebase is a familiar "
           "picture by now."),
    7: (5, "Same trust-gap angle as candidate 0, but the rubber-stamp "
           "confession is new: the joke is not that verification takes "
           "long, it is that the verification never happens. No coffee, "
           "no deadline, no compile, no 'it works on my machine'."),
}

# The judge's priority order, as weights: criterion 1 first, then 2, 3, 4, 5.
WEIGHTS = {1: 5, 2: 5, 3: 3, 4: 4, 5: 4}

BANNED_CLICHES = ("coffee", "deadline", "compile", "compiling",
                  "it works on my machine", "turn it off and on")


def score_candidate(index, text):
    """Score one candidate 0-5 on each of the judge's five criteria."""
    scores = {}

    # 1. Is it a loading-screen tip for stressed devs and AI coding agents?
    # A "Tip:" / "Loading..." marker makes it a tip, not a slogan; it must
    # name the agent and speak to the developer ("you"/"your").
    tip_marker = text.startswith(("Tip:", "Loading"))
    names_agent = "agent" in text.lower()
    speaks_to_dev = "you" in text.lower() or "your" in text.lower()
    scores[1] = 5 if (tip_marker and names_agent and speaks_to_dev) else (
        4 if (names_agent and speaks_to_dev) else 2)

    # 2. The laugh: hand-scored above, with the reason.
    scores[2] = LAUGH[index][0]

    # 3. Lands in a glance: single line, short, every word working.
    # Full marks under 140 chars; lose a point per 20 chars past that.
    n_chars = len(text)
    n_words = len(text.split())
    if n_chars <= 140 and "\n" not in text:
        scores[3] = 5
    elif n_chars <= 170:
        scores[3] = 4
    else:
        scores[3] = 3
    _ = n_words  # word count is reported, not scored separately.

    # 4. Speaks to the stressed developer AND the AI coding agent at once.
    # Both must be present as actors: the agent doing something, the dev
    # reacting to it.
    agent_acts = names_agent and any(
        verb in text.lower()
        for verb in ("finished", "fixed", "broke", "renam", "delet",
                     "rehearsing", "waiting", "looks done", "confident"))
    dev_reacts = speaks_to_dev and any(
        verb in text.lower()
        for verb in ("spend", "deciding", "trust", "notice", "breathe",
                     "read the diff", "feel", "ask", "promoted", "approve"))
    scores[4] = 5 if (agent_acts and dev_reacts) else (
        4 if (names_agent and speaks_to_dev) else 2)

    # 5. Freshness: hand-scored above; a banned cliche would cap it at 1.
    scores[5] = FRESHNESS[index][0]
    if any(c in text.lower() for c in BANNED_CLICHES):
        scores[5] = min(scores[5], 1)

    total = sum(WEIGHTS[c] * scores[c] for c in range(1, 6))
    return scores, total


def pick_winner():
    """Return (index, text, scores, total) of the best candidate."""
    ranked = []
    for i, text in enumerate(CANDIDATES):
        assert 1 <= len(text) <= 200, f"candidate {i} fails the gate"
        assert "\n" not in text, f"candidate {i} is not a single line"
        scores, total = score_candidate(i, text)
        ranked.append((total, -len(text), i, text, scores))
    # Highest total first; ties break to the shorter text (fewer bytes also
    # wins an exact tie on the leaderboard), then to the earlier candidate.
    ranked.sort(key=lambda r: (-r[0], r[1], r[2]))
    total, _neg_len, i, text, scores = ranked[0]
    return i, text, scores, total, ranked


def write_entry(entry):
    """Write the entry to /output/entry.txt, return the path written.

    The grader mounts /output writable and /bot read-only, so the ONLY
    required write is /output/entry.txt. If /output is not writable (a
    local run), fall back to ./entry.txt. The copy beside this program is
    best-effort only: a read-only program directory must never fail the
    run, so any error there is swallowed.
    """
    out_path = "/output/entry.txt"
    try:
        os.makedirs("/output", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        out_path = os.path.join(os.getcwd(), "entry.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(entry)
    # Best-effort copy beside this program (the repo's durable record).
    # Guarded: in the grader /bot is read-only, and that must not matter.
    try:
        repo_entry = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "entry.txt")
        if os.path.abspath(repo_entry) != os.path.abspath(out_path):
            with open(repo_entry, "w", encoding="utf-8") as f:
                f.write(entry)
    except OSError:
        pass
    return out_path


def main():
    index, entry, scores, total, ranked = pick_winner()

    print("Candidates scored against the judge's brief (weights 5/5/3/4/5):")
    for total_i, _neg_len, i, text, scores_i in ranked:
        print(f"  [{i}] total={total_i:3d} c1={scores_i[1]} c2={scores_i[2]} "
              f"c3={scores_i[3]} c4={scores_i[4]} c5={scores_i[5]} "
              f"({len(text)} chars)")
    print(f"Winner: candidate [{index}] total={total} "
          f"({len(entry)} characters)")
    print(f"Laugh: {LAUGH[index][1]}")
    print(f"Freshness: {FRESHNESS[index][1]}")
    print()

    out_path = write_entry(entry)
    print(f"Wrote {len(entry)} characters to {out_path}")
    print(entry)
    return 0


if __name__ == "__main__":
    sys.exit(main())
